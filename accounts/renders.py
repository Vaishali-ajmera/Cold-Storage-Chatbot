import json

from rest_framework import renderers


class UserRenderer(renderers.JSONRenderer):
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = {
            "data": {},
            "status": True,
            "message": "",
        }

        if renderer_context:
            response_status = renderer_context.get("response").status_code

            if response_status >= 400:
                response["status"] = False

                if isinstance(data, dict):
                    message = (
                        data.get("message")
                        or data.get("detail")
                        or data.get("error")
                        or data.get("non_field_errors")
                    )

                    # If message is still None or empty, try to extract first field error
                    if not message:
                        for field, errors in data.items():
                            if isinstance(errors, list) and errors:
                                message = errors[0]
                                break
                            elif isinstance(errors, str):
                                message = errors
                                break

                    # If message is still a dict or list, convert to string
                    if isinstance(message, dict):
                        # Extract first error from nested dictionary
                        for field, errors in message.items():
                            if isinstance(errors, list) and errors:
                                message = errors[0]
                                break
                            elif isinstance(errors, str):
                                message = errors
                                break
                    elif isinstance(message, list) and message:
                        message = message[0]

                    # Ensure message is always a string
                    response["message"] = (
                        str(message) if message else "Something went wrong"
                    )
                else:
                    response["message"] = "Something went wrong"

                response["data"] = {}

            else:
                if isinstance(data, dict):
                    # Preferably fetch and pop 'message' first to avoid data nesting
                    response["message"] = data.pop("message", "Request was successful")

                    # If after popping, the remaining dict is exactly {"data": [...]}, flatten it
                    if list(data.keys()) == ["data"]:
                        response["data"] = data["data"]
                    else:
                        response["data"] = data

                elif isinstance(data, list):
                    response["data"] = data
                    response["message"] = "Request was successful"

                else:
                    response["data"] = data
                    response["message"] = "Request was successful"

        return json.dumps(response)
