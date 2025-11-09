import base64
import json
import traceback
from io import BytesIO
from typing import Annotated, List, Optional, Union

import PIL.Image
import requests
from pydantic import BaseModel

from marker.schema.blocks import Block
from marker.services import BaseService


def flatten_schema(schema):
    if not isinstance(schema, dict):
        return schema

    defs = schema.pop('$defs', {})

    def resolve_refs(obj):
        if isinstance(obj, dict):
            if '$ref' in obj:
                ref_name = obj['$ref'].split('/')[-1]
                return resolve_refs(defs.get(ref_name, {}))
            else:
                return {k: resolve_refs(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [resolve_refs(item) for item in obj]
        return obj

    return resolve_refs(schema)


class OllamaService(BaseService):
    ollama_base_url: Annotated[
        str,
        "The base url to use for ollama. No trailing slash."
    ] = "http://localhost:11434"
    ollama_model: Annotated[
        str,
        "The model name to use for ollama."
    ] = "llama3.2-vision"

    def image_to_base64(self, image: PIL.Image.Image) -> str:
        image_bytes = BytesIO()
        image.save(image_bytes, format="PNG")
        return base64.b64encode(image_bytes.getvalue()).decode("utf-8")

    def __call__(
        self,
        prompt: str,
        image: Optional[Union[PIL.Image.Image, List[PIL.Image.Image]]],
        block: Optional[Block],
        response_schema: type[BaseModel],
        max_retries: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        url = f"{self.ollama_base_url}/api/generate"
        headers = {"Content-Type": "application/json"}

        # Generate and flatten the JSON schema to resolve $refs
        schema = response_schema.model_json_schema()
        schema = flatten_schema(schema)

        format_schema = {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", []),
        }

        if image is None:
            image_list = []
        elif isinstance(image, list):
            image_list = image
        else:
            image_list = [image]

        image_bytes = [self.image_to_base64(img) for img in image_list]

        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": format_schema,
            "images": image_bytes,
        }

        try:
            # Log request details for debugging
            print("Ollama API Request to:", url)
            print("Request headers:", headers)
            #print("Request payload:", json.dumps(payload, indent=2))  # Limit output length
            print(f"Request payload: {payload["prompt"]} - format: {payload["format"]}")
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()

            response_data = response.json()
            #print("Ollama API Response data:", json.dumps(response_data, indent=2))
            print(f"Ollama API Response data: {response_data}")
            total_tokens = (
                response_data.get("prompt_eval_count", 0)
                + response_data.get("eval_count", 0)
            )

            if block is not None:
                block.update_metadata(llm_request_count=1, llm_tokens_used=total_tokens)

            data = response_data.get("response", "{}")
            return json.loads(data)

        except requests.HTTPError as http_err:
            print(f"Ollama HTTPError: {http_err} - Response content: {response.text}")
        except Exception as e:
            print(f"Ollama inference failed: {e}")
            print(traceback.format_exc())

        return {}
