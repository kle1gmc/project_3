from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QTextEdit
import requests
import json


ACCESS_TOKEN = "access_token"

headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0NzY1NTE5NSwianRpIjoiZTE2ODZjMDMtZWQ3OC00ZDZiLTg0MTAtOGZjOTE3MDdlNzU1IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjQiLCJuYmYiOjE3NDc2NTUxOTUsImNzcmYiOiJmYzEyNmY2My1lYzllLTQzYTUtYWQ0Ni1mZmYzNDE4ZDM4ZWEiLCJleHAiOjE3NDc2NTg3OTV9.ACXE6EjpRYzH9GiOkQucOhf_SwgKpO0lX2vsRvuyXx8",
    "Content-Type": "application/json"
}

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("CRUD: Товары")

        layout = QVBoxLayout()

        self.input_id = QLineEdit(self)
        self.input_id.setPlaceholderText("ID товара (для удаления/обновления)")

        self.input_name = QLineEdit(self)
        self.input_name.setPlaceholderText("Название товара")

        self.input_price = QLineEdit(self)
        self.input_price.setPlaceholderText("Цена товара")

        self.input_quantity = QLineEdit(self)
        self.input_quantity.setPlaceholderText("Количество")

        self.btn_add = QPushButton("Добавить товар", self)
        self.btn_add.clicked.connect(self.add_product)

        self.btn_get = QPushButton("Показать товары", self)
        self.btn_get.clicked.connect(self.get_products)

        self.btn_delete = QPushButton("Удалить товар по ID", self)
        self.btn_delete.clicked.connect(self.delete_product)

        self.btn_update = QPushButton("Обновить товар по ID", self)
        self.btn_update.clicked.connect(self.update_product)

        self.output = QTextEdit(self)
        self.output.setReadOnly(True)

        layout.addWidget(self.input_id)
        layout.addWidget(self.input_name)
        layout.addWidget(self.input_price)
        layout.addWidget(self.input_quantity)
        layout.addWidget(self.btn_add)
        layout.addWidget(self.btn_update)
        layout.addWidget(self.btn_delete)
        layout.addWidget(self.btn_get)
        layout.addWidget(self.output)

        self.setLayout(layout)
        self.resize(350, 500)

    def add_product(self):
        name = self.input_name.text().strip()
        price = self.input_price.text().strip()
        quantity = self.input_quantity.text().strip()

        if name and price and quantity:
            try:
                response = requests.post(
                    "http://localhost:5000/api/products",
                    json={  
                        "name": name,
                        "price": float(price),
                        "quantity": int(quantity)
                    },
                    headers=headers  
                )

                try:
                    json_data = response.json()
                    formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
                    self.output.append(f"Добавление товара:\n{response.status_code} {formatted_json}")
                except Exception:
                    self.output.append(f"Добавление товара:\n{response.status_code} {response.text}")

            except Exception as e:
                self.output.append(f"Ошибка при подключении к серверу: {e}")
        else:
            self.output.append("Ошибка: Заполните все поля для добавления.")

    def get_products(self):
        try:
            response = requests.get("http://localhost:5000/api/products", headers=headers)
            if response.status_code == 200:
                products = response.json().get('products', [])
                self.output.clear()
                if not products:
                    self.output.append("Товары не найдены.")
                    return
                for p in products:
                    self.output.append(f"{p['id']}. {p['name']} - {p['price']} руб. (x{p['quantity']})")
            else:
                self.output.append(f"Ошибка при получении товаров: {response.status_code} {response.text}")
        except Exception as e:
            self.output.append(f"Ошибка при получении товаров: {e}")

    def delete_product(self):
        product_id = self.input_id.text().strip()
        if not product_id:
            self.output.append("Введите ID для удаления.")
            return
        try:
            response = requests.delete(f"http://localhost:5000/api/products/{product_id}", headers=headers)
            self.output.append(f"Удаление товара:\n{response.status_code} {response.text}")
        except Exception as e:
            self.output.append(f"Ошибка при удалении товара: {e}")

    def update_product(self):
        product_id = self.input_id.text().strip()
        name = self.input_name.text().strip()
        price = self.input_price.text().strip()
        quantity = self.input_quantity.text().strip()

        if not (product_id and name and price and quantity):
            self.output.append("Заполните ID, название, цену и количество для обновления.")
            return

        try:
            data = {
                "name": name,
                "price": float(price),
                "quantity": int(quantity)
            }
            response = requests.put(f"http://localhost:5000/api/products/{product_id}", json=data, headers=headers)
            self.output.append(f"Обновление товара:\n{response.status_code} {response.text}")
        except Exception as e:
            self.output.append(f"Ошибка при обновлении товара: {e}")

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
