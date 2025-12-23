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

                    # If no standard error key found, try to extract first field error
                    if not message:
                        for field, errors in data.items():
                            if isinstance(errors, list) and errors:
                                message = errors[0]
                                break
                            elif isinstance(errors, str):
                                message = errors
                                break

                    response["message"] = message or "Something went wrong"
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
