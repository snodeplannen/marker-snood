@echo off
setlocal

rem De root directory om te doorzoeken
set "rootdir=C:\projecten\marker-snood\ebook"

rem Recursief door alle bestanden lopen
for /R "%rootdir%" %%f in (*) do (
    echo Verwerk bestand: %%f
    rem Plaats hier de opdracht om het bestand te verwerken
    rem Bijvoorbeeld: type "%%f"
    uv run marker_single --llm_service=marker.services.ollama.OllamaService --ollama_base_url http://192.168.50.30:11434 --OllamaService_timeout 60 --OllamaService_max_retries 7 --OllamaService_retry_wait_time 6 --OllamaService_max_output_tokens 9000 --model_max_length 12000 --ollama_model=gemma3:12b-it-qat  --use_llm --LLMImageDescriptionProcessor_use_llm  --disable_image_extraction --TableConverter_use_llm  --ExtractionConverter_use_llm  --LLMTableMergeProcessor_use_llm  --LLMPageCorrectionProcessor_use_llm --LLMComplexRegionProcessor_use_llm --max_concurrency 1 "%%f"
)

endlocal
pause




