class Luggage:
    def __init__(self, weight=0, cost=0.0):
        self.weight = weight  # Trọng lượng hành lý (kg)
        self.cost = cost      # Chi phí hành lý (đơn vị tiền tệ)

    def get_info(self):
        return {
            "weight": self.weight,
            "cost": self.cost,
        }


class PassengerInfo:
    def __init__(self, passenger_id=0, last_name="", first_name="", phone="", email="",
                 id_number="", birth_date=None, luggage=None, luggage_return=None):
        if birth_date is None:
            birth_date = {"day": "", "month": "", "year": ""}

        self.passenger_id = passenger_id
        self.last_name = last_name
        self.first_name = first_name
        self.phone = phone
        self.email = email
        self.id_number = id_number
        self.birth_date = birth_date
        self.luggage = luggage if luggage else Luggage()  # Hành lý cho chuyến đi
        self.luggage_return = luggage_return  # Hành lý cho chuyến về, nếu có

    def get_info(self):
        return {
            "passenger_id": self.passenger_id,
            "last_name": self.last_name,
            "first_name": self.first_name,
            "phone": self.phone,
            "email": self.email,
            "id_number": self.id_number,
            "birth_date": self.birth_date,
            "luggage": self.luggage.get_info() if self.luggage else None,  # Hành lý chuyến đi
            "luggage_return": self.luggage_return.get_info() if self.luggage_return else None  # Hành lý chuyến về
        }

