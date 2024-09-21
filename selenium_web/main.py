from booking_bot import BookingBot

if __name__ == "__main__":
    bot = BookingBot()
    bot.open_site("https://www.booking.com")
    bot.select_date()  # Ensure this date exists in the calendar
    bot.search_city("New York")
    bot.scrape_hotels()
    bot.close()
