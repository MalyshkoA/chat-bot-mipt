import sqlite3
import unittest
from unittest import mock
import main as bot

class UserTestCase(unittest.TestCase):

    test_user_id = 9999999999999
    
    def setUp(self):
        conn = sqlite3.connect('./app_data/database.db')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY)')
        conn.commit()
        conn.close()

    def tearDown(self):
        conn = sqlite3.connect('./app_data/database.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE telegram_id = ?', (self.test_user_id,))
        conn.commit()
        conn.close()

    def test_check_user_data(self):
        user = bot.User(self.test_user_id)
        user.create_user_record()
        result = user.check_user_data()
        self.assertEqual(result, (self.test_user_id,))

    def test_create_user_record(self):
        user = bot.User(self.test_user_id)
        self.assertIsNone(user.check_user_data())
        inserted_id = user.create_user_record()
        self.assertIsNotNone(inserted_id)
        self.assertIsNotNone(user.check_user_data())
        self.assertEqual(inserted_id, user.telegram_id)

class StockTestCase(unittest.TestCase):
    
    test_user_id = 9999999999999
    
    test_stock = bot.Stock(test_user_id, 'AAPL', 10, 100, '2023-07-13 03:09:10.579702')

    def setUp(self):
        conn = sqlite3.connect('./app_data/database.db')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS users (telegram_id INTEGER PRIMARY KEY)')
        cursor.execute('CREATE TABLE IF NOT EXISTS stocks (owner_id INTEGER, stock_id TEXT, quantity INTEGER, unit_price REAL, purchase_date TIMESTAMP, FOREIGN KEY (owner_id) REFERENCES users(telegram_id) ON DELETE CASCADE)') 
        conn.commit()
        conn.close()
    
    def tearDown(self):
        conn = sqlite3.connect('./app_data/database.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE telegram_id = ?', (self.test_user_id,))
        cursor.execute('DELETE FROM stocks WHERE owner_id = ?', (self.test_user_id,))
        conn.commit()
        conn.close()
    
    def test_add_stock(self):
        bot.Stock.add_stock(self.test_stock)
        conn = sqlite3.connect('./app_data/database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM stocks WHERE owner_id = ?', (self.test_user_id,))
        result = cursor.fetchall()
        conn.close()
        self.assertNotEqual(result, [])
        self.assertEqual(result[0], (self.test_stock.owner_id, self.test_stock.stock_id, self.test_stock.quantity,self.test_stock.unit_price, self.test_stock.purchase_date))
    
    def test_get_user_stock(self):
        bot.Stock.add_stock(self.test_stock)
        result = bot.Stock.get_user_stocks(self.test_user_id)
        self.assertIsNotNone(result)
        self.assertIn(self.test_stock, result)

class CheckStockExistenceTestCase(unittest.TestCase):
    
    test_stock_id = "AAPL"
    test_url = f"https://iss.moex.com/iss/securities/{test_stock_id}.json"
    test_response_json = {"boards": {"data": [["AAPL"]]}}

    def test_check_stock_existence(self):        
        
        with mock.patch('requests.get') as mock_get:
            
            mock_response_success = mock.Mock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = self.test_response_json
            
            mock_response_error = mock.Mock()
            mock_response_error.status_code = 400
            mock_response_error.json.return_value = None

            mock_get.return_value = mock_response_success
            result_success = bot.check_stock_existence(self.test_stock_id)
            self.assertTrue(result_success)
            mock_get.assert_called_once_with(self.test_url)
                
            mock_get.return_value = mock_response_error
            result_error = bot.check_stock_existence(self.test_stock_id)
            self.assertFalse(result_error)
            mock_get.assert_called_with(self.test_url)

class GetStockPriceRuTestCase(unittest.TestCase):
    
    test_stock_id = "AAPL"
    test_url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{test_stock_id}.json?iss.only=securities&securities.columns=PREVPRICE,CURRENCYID"
    test_response_json = {
        "securities": {
            "data": [
                [100.0, "SUR"]
            ]
        }
    }

    def test_get_stock_price_ru(self):
        
        with mock.patch('requests.get') as mock_get:
            
            mock_response_success = mock.Mock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = self.test_response_json
            
            mock_response_error = mock.Mock()
            mock_response_error.status_code = 400
            mock_response_error.json.return_value = None

            mock_get.return_value = mock_response_success
            result_success = bot.get_stock_price_ru(self.test_stock_id)
            self.assertEqual(result_success, "100.0 RUB")

            mock_get.return_value = mock_response_error
            result_error = bot.get_stock_price_ru(self.test_stock_id)
            self.assertFalse(result_error)

class GetStockPriceWorldTestCase(unittest.TestCase):

    test_stock_id = "AAPL"

    def test_get_stock_price_world(self):
        
        with mock.patch('yfinance.Ticker') as mock_ticker:
            mock_ticker_instance = mock_ticker.return_value
            mock_ticker_instance.info = {
                'currency': 'USD',
                'currentPrice': 150.0
            }
            
            result = bot.get_stock_price_world(self.test_stock_id)
            self.assertEqual(result, "150.0 USD")
            mock_ticker.assert_called_once_with(self.test_stock_id)

if __name__ == '__main__':
    unittest.main()
