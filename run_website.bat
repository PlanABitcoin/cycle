@echo off

cd /d "G:\My Drive\binatix\crypto\Binance_aggTrades_10s_bars_parquet\Bitcoin_book"

echo ========================================== >> website_log.txt
echo %date% %time% Starting update >> website_log.txt

py -3 main_website_run_all.py >> website_log.txt 2>&1

echo %date% %time% Finished update >> website_log.txt
echo. >> website_log.txt