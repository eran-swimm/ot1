from . import models
import datetime

# Run using:
# python manage.py check

MAX_MONTH = 3
MIN_MONTHLY_TRIP_COUNT = 2500
MAX_MONTHLY_TRIP_COUNT = 3500
MIN_DAILY_TRIP_COUNT = 100
MAX_DAILY_TRIP_COUNT = 300
MIN_MONTHLY_VALID_TRIP_RATIO = 0.97
MIN = 0
MAX = 1
MONTHLY_SAMPLES = {
  'default' : [150, 1000],
  'Haifa Center HaShmona': [800, 2500],
  'Haifa Bat Gallim': [800, 2500],
  "Haifa Hof HaKarmel (Razi'el)": [800, 2500],
  'Tel Aviv - University': [1200, 6000],
  'Tel Aviv Center - Savidor': [1200, 6000],
  'Tel Aviv HaShalom': [1200, 6000],
  'Tel Aviv HaHagana': [1200, 6000],
  'Jerusalem Malha': [20, 300],
  'Jerusalem Biblical Zoo': [20, 300],
  'Lod': [300, 1300],
  'Dimona': [30, 60]
}

def run():
  check_months()
  # TODO: Enable this once we get daily data for Jan-Mar 2017
  check_days()
  check_valid_percent_per_month()
  check_samples_per_station_per_month()


def check_months():
  errors = []
  for month in range(1, MAX_MONTH + 1):
    date1 = datetime.datetime(2017, month, 1)
    date2 = datetime.datetime(2017, month + 1, 1)
    trip_count = models.Trip.objects.filter(date__gte=date1, date__lt=date2).count()
    if trip_count < MIN_MONTHLY_TRIP_COUNT:
      errors.append("Trip count {} for month {} is lower than minimum {}".format(trip_count, month, MIN_MONTHLY_TRIP_COUNT))
    if trip_count > MAX_MONTHLY_TRIP_COUNT:
      errors.append("Trip count {} for month {} is higher than maximum {}".format(trip_count, month, MAX_MONTHLY_TRIP_COUNT))
  if errors:
    for error in errors:
      print(error)
  else:
    print("No errors in months")


def check_days():
  errors = []
  date1 = datetime.datetime(2017, 1, 1)
  date2 = datetime.datetime(2017, MAX_MONTH + 1, 1)    
  for day in daterange(date1, date2):
    trip_count = models.Trip.objects.filter(date__gte=day, date__lt=day + datetime.timedelta(days=1)).count()
    if trip_count < MIN_DAILY_TRIP_COUNT:
      errors.append("Trip count {} for day {} is lower than minimum {}".format(trip_count, day, MIN_DAILY_TRIP_COUNT))
    if trip_count > MAX_DAILY_TRIP_COUNT:
      errors.append("Trip count {} for day {} is higher than maximum {}".format(trip_count, day, MAX_DAILY_TRIP_COUNT))
  if errors:
    for error in errors:
      print(error)
  else:
    print("No errors in days")


def check_valid_percent_per_month():
  errors = []
  for month in range(1, MAX_MONTH + 1):
    date1 = datetime.datetime(2017, month, 1)
    date2 = datetime.datetime(2017, month + 1, 1)
    all_trip_count = models.Trip.objects.filter(date__gte=date1, date__lt=date2).count()
    valid_trip_count = models.Trip.objects.filter(date__gte=date1, date__lt=date2, valid=True).count()
    valid_trip_ratio = valid_trip_count/all_trip_count
    if valid_trip_ratio < MIN_MONTHLY_VALID_TRIP_RATIO:
      errors.append("Valid trip ratio {} for month {} is lower than minimum {}".format(valid_trip_ratio, month, MIN_MONTHLY_VALID_TRIP_RATIO))
  if errors:
    for error in errors:
      print(error)
  else:
    print("No errors in months validity")


def check_samples_per_station_per_month():
  errors = []
  stops = list(models.Stop.objects.all())
  for month in range(1, MAX_MONTH + 1):
    for stop in stops:
      date1 = datetime.datetime(2017, month, 1)
      date2 = datetime.datetime(2017, month + 1, 1)
      samples_count = models.Sample.objects.filter(trip__date__gte=date1, trip__date__lt=date2, stop__gtfs_stop_id=stop.gtfs_stop_id).count()
      min_monthly_samples = MONTHLY_SAMPLES[stop.english][MIN] if stop.english in MONTHLY_SAMPLES else MONTHLY_SAMPLES['default'][MIN]
      max_monthly_samples = MONTHLY_SAMPLES[stop.english][MAX] if stop.english in MONTHLY_SAMPLES else MONTHLY_SAMPLES['default'][MAX]
      if samples_count < min_monthly_samples:
        errors.append("Samples count {} on month {} for stop {} ({}) is lower than minimum {}".format(samples_count, month, stop.gtfs_stop_id, stop.english, min_monthly_samples))
      if samples_count > max_monthly_samples:
        errors.append("Samples count {} on month {} for stop {} ({}) is higher than maximum {}".format(samples_count, month, stop.gtfs_stop_id, stop.english, max_monthly_samples))
  if errors:
    for error in errors:
      print(error)
  else:
    print("No errors in samples per station per month")

def daterange(start_date, end_date):
  for n in range(int ((end_date - start_date).days)):
    yield start_date + datetime.timedelta(n)
