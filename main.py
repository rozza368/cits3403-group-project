from app import create_app, db
from app.config import DevelopmentConfig, TestConfig

app = create_app(DevelopmentConfig)

testapp = create_app(TestConfig)

if __name__ == "__main__":
    app.run(debug=False)