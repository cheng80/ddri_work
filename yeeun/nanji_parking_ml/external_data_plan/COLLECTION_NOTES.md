# External Data Collection Notes

1. Fill API keys in a local .env file and do not commit secrets.
2. Save untouched downloads into data/raw/ and keep the original filenames when possible.
3. Save cleaned model-ready files into data/processed/.
4. Keep timestamp timezone consistent, preferably Asia/Seoul.
5. Prioritize 2023, 2024, and 2025 rows when filtering raw files.
6. Start with camping or parking target data before enriching with weather, holidays, and performance schedules.
7. The KOPIS performance APIs are useful for building event flags around Nanji and Hangang demand spikes.