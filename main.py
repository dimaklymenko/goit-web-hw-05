import asyncio
from datetime import datetime, timedelta
import aiohttp
import sys


class CurrencyRateFetcher:
    API_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date={date}"

    def __init__(self, max_days=10):
        self.max_days = max_days

    @staticmethod
    async def fetch_rates(session, date):
        url = CurrencyRateFetcher.API_URL.format(date=date.strftime("%d.%m.%Y"))
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    raise Exception(f"Error fetching data: {response.status}")
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {e}")

    @staticmethod
    def parse_rates(data, currencies=("USD", "EUR")):
        try:
            exchange_date = data.get("date", "Unknown date")
            rates = {currency: None for currency in currencies}

            for rate in data.get("exchangeRate", []):
                if rate.get("currency") in currencies:
                    rates[rate["currency"]] = {
                        "buy": rate.get("purchaseRate", "N/A"),
                        "sell": rate.get("saleRate", "N/A"),
                    }

            return exchange_date, rates
        except KeyError:
            raise Exception("Invalid data format from API")

    @staticmethod
    def format_rates_for_console(parsed_results):
        formatted = []
        for date, rates in parsed_results:
            if date == "Error":
                formatted.append(f"Error fetching data: {rates}")
            else:
                day_info = [f"Date: {date}"]
                for currency, rate in rates.items():
                    if rate:
                        day_info.append(
                            f"  {currency}: Buy - {rate['buy']}, Sell - {rate['sell']}"
                        )
                    else:
                        day_info.append(f"  {currency}: No data available")
                formatted.append("\n".join(day_info))
                formatted.append("-" * 40)
        return "\n\n".join(formatted)

    async def get_rates_for_last_days(self, days):
        if days > self.max_days:
            raise ValueError(f"Cannot fetch data for more than {self.max_days} days.")

        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                tasks.append(self.fetch_rates(session, date))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            parsed_results = []
            for result in results:
                if isinstance(result, Exception):
                    parsed_results.append(("Error", str(result)))
                else:
                    parsed_results.append(self.parse_rates(result))

            return parsed_results


async def main():
    if len(sys.argv) != 2:
        print("Usage: python main4.py <number_of_days>")
        sys.exit(1)

    try:
        days = int(sys.argv[1])
    except ValueError:
        print("Please provide a valid number of days.")
        sys.exit(1)

    fetcher = CurrencyRateFetcher()

    try:
        results = await fetcher.get_rates_for_last_days(days)
        print(fetcher.format_rates_for_console(results))
    except ValueError as e:
        print(f"\n{e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
