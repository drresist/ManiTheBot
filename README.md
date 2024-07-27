# Mani The Bot

## Overview

TG-Mani Bot is a simple expense tracking bot built using Python and the Telebot library. It allows authorized users to track their income and expenses by selecting categories and entering amounts.

## Features

* User authentication: Only allowed users can use the bot.
* Expense tracking: Users can select from predefined categories (Expense, Income) and enter amounts.
* Payment addition: Users can add payments to their expense tracker.
* Statistics: The bot will generate summary statistics for income and expenses.

## Usage

To start using the bot, simply send a `/start` command. You will then be presented with an initial keyboard where you can select between Expense and Income categories.

### Expenses and Income

* To track an expense or income, select the corresponding category from the keyboard.
* Enter the amount of money in your message.
* The bot will prompt you to enter the category ID (if selected).
* Once you have entered all required information, the bot will add the payment to your tracker.

### Statistics and Charts

The bot generates summary statistics for income and expenses. You can access these by sending a `/stat` command.

## Notes

* The bot is designed for personal use only.
* Please ensure that you are an authorized user before using the bot.
* If you encounter any errors or issues, please try again or contact the bot administrator.

### Authors

This bot was developed by MFesenko.

### License

The TG-Mani Bot is licensed under the MIT License.
