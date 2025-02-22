class FlightDetail:
    def __init__(self, departure_time="", departure_date="", arrival_time="", arrival_date="",
                 departure_airport=None, arrival_airport=None, airline="", logo="", duration="",
                 number_day=0, stops=0):
        if departure_airport is None:
            departure_airport = {}
        if arrival_airport is None:
            arrival_airport = {}

        self.departure_time = departure_time
        self.departure_date = departure_date
        self.arrival_time = arrival_time
        self.arrival_date = arrival_date
        self.departure_airport = departure_airport
        self.arrival_airport = arrival_airport
        self.airline = airline
        self.logo = logo
        self.duration = duration
        self.number_day = number_day
        self.stops = stops



    def get_info(self):
        return {
            "departure_time": self.departure_time,
            "departure_date": self.departure_date,
            "arrival_time": self.arrival_time,
            "arrival_date": self.arrival_date,
            "departure_airport": self.departure_airport,
            "arrival_airport": self.arrival_airport,
            "airline": self.airline,
            "logo": self.logo,
            "duration": self.duration,
            "number_day": self.number_day,
            "stops": self.stops,
        }


class FlightInfo:
    def __init__(self, ma_chuyen_bay="", details_flight=None, stops=0, logo="", number_day=0,
                 airline="", duration="", departure_time="", arrival_time="", airline_code="", price = 0):
        if details_flight is None:
            details_flight = []

        self.ma_chuyen_bay = ma_chuyen_bay
        self.details_flight = details_flight
        self.stops = stops
        self.logo = logo
        self.number_day = number_day
        self.airline = airline
        self.duration = duration
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.airline_code = airline_code
        self.price = price

    def get_info(self):
        return {
            "ma_chuyen_bay": self.ma_chuyen_bay,
            "details_flight": self.details_flight,
            "stops": self.stops,
            "logo": self.logo,
            'number_day': self.number_day,
            "airline": self.airline,
            "duration": self.duration,
            'departureTime': self.departure_time,
            'arrivalTime': self.arrival_time,
            "airline_code": self.airline_code,
            "price": self.price
        }

