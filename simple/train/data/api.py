from models import Sample, Trip, Route
from django.http import HttpResponse, Http404
from django.core import serializers
from django.db.models import Q
import itertools, datetime, json
from django.utils.timezone import make_naive, get_current_timezone
from collections import Counter
from django.conf import settings


def json_resp(obj, status=200):
    import json

    return HttpResponse(content=json.dumps(obj), content_type='application/json')


def show_sample(req):
    try:
        sample = Sample.objects.filter(stop_id=req.GET.get('stop_id'), valid=True, is_real_stop=True)

        response = HttpResponse(serializers.serialize('json', sample))
        print(response)
        return response
    except Exception as e:
        print(e)


def get_departure_hour(sample):
    return make_naive(sample.exp_departure, get_current_timezone()).hour


def get_stops(req):
    import services

    stops = services.get_stops()
    stops.sort(key=lambda x: x['stop_name'])
    return json_resp(stops)


def get_relevant_routes(origin, destination, fromTime, toTime, days):
    routes = Trip.objects.raw('''SELECT id, stop_ids
        FROM public.data_trip
        WHERE valid
        AND ARRAY[%s::int,%s::int] <@ stop_ids
        AND EXTRACT(dow FROM start_date)::int = ANY(%s)
        ''', [origin, destination, days])

    trips = [route.id for route in routes if route.stop_ids.index(int(origin)) < route.stop_ids.index(int(destination))]

    samples = list(
        Sample.objects.filter(Q(stop_id=destination) | Q(stop_id=origin)).filter(trip_name__in=trips).order_by(
            'trip_name'))

    filteredSamples = []
    for firstSample, secondSample in itertools.izip(samples[::2], samples[1::2]):
        # if(firstSample.id == 14):
        # print(firstSample.id, make_naive(firstSample.exp_departure, get_current_timezone()))
        if (firstSample.stop_id == origin and fromTime <= get_departure_hour(firstSample) <= toTime) or \
                (secondSample.stop_id == origin and fromTime <= get_departure_hour(secondSample) <= toTime):
            filteredSamples.append(
                (firstSample, secondSample) if firstSample.stop_id == origin else (secondSample, firstSample))

    return filteredSamples


def get_relevant_routes_from_request(req):
    try:
        origin = int(req.GET.get('from'))
        destination = int(req.GET.get('to'))
        fromTime = int(req.GET.get('from_time') or 0)
        toTime = int(req.GET.get('to_time') or 23)
        days = req.GET.get('days')
        days = (days and map(int, days.split(','))) or list(range(0, 6))

        return get_relevant_routes(origin, destination, fromTime, toTime, days)

    except Exception as e:
        print(e)


def get_delay_from_data(samples):
    size = len(samples)

    if size == 0:
        return {}

    delays = [sample[1].delay_arrival or 0 for sample in samples]
    average = sum(delays) / size
    minimum = min(delays)
    maximum = max(delays)

    minTrips = [sample[1].trip_name for sample in samples if sample[1].delay_arrival == minimum]
    maxTrips = [sample[1].trip_name for sample in samples if sample[1].delay_arrival == maximum]

    return {'min': {
        'duration': minimum,
        'trips': minTrips
    }, 'max': {
        'duration': maximum,
        'trips': maxTrips
    },
            'average': average
    }


def get_delay(req):
    samples = get_relevant_routes_from_request(req)
    return HttpResponse(json.dumps(get_delay_from_data(samples)))


def get_delay_over_total_duration_from_data(samples):
    delay = 0
    duration = datetime.timedelta()
    for sample in samples:
        if len(sample) != 2:
            continue

        delay += (sample[1].delay_arr0ival or 0)
        duration += sample[1].exp_arrival - sample[0].exp_departure
    res = delay / duration.total_seconds()
    return res


def get_delay_over_total_duration(req):
    samples = get_relevant_routes_from_request(req)
    return HttpResponse(get_delay_over_total_duration_from_data(samples))


def get_trip(req, trip_id):
    from models import Trip

    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        return json_resp({'error': '404',
                          'trip_id': trip_id},
                         status=404)
    return json_resp(trip.to_json());


def get_delay_buckets(req):
    if req.GET.get('from'):  # TODO: check all routes
        samples = get_relevant_routes_from_request(req)
        delays = [sample[1].delay_arrival or 0 for sample in samples]
        res = {}
        for key, value in dict(Counter([delay // 300 for delay in delays])).iteritems():
            res[key * 5] = value
        return HttpResponse(res)


def get_delay_over_threshold_from_data(samples, threshold):
    delaysOverThreshold = len([sample[1].delay_arrival for sample in samples if sample[1].delay_arrival >= threshold])
    res = {'nominal': delaysOverThreshold, 'proportional': float(delaysOverThreshold) / len(samples)}
    return res


def get_delay_over_threshold(req):
    samples = get_relevant_routes_from_request(req)
    threshold = int(req.GET.get('threshold'))
    return HttpResponse(json.dumps(get_delay_over_threshold_from_data(samples, threshold)))


def get_worst_station_from_data(samples):
    trips = [sample[0].trip_name for sample in samples]
    allStops = Sample.objects.filter(trip_name__in=trips).filter(delay_arrival__gt=600).order_by('trip_name')
    worstSamples = []
    for trip, samples in itertools.groupby(allStops, lambda sample: sample.trip_name):
        worstSamples.append(max(samples, key=lambda sample: sample.delay_arrival))
    return dict(Counter([sample.stop_id for sample in worstSamples]))


def get_worst_station_in_route_helper(req):
    samples = get_relevant_routes_from_request(req)
    return get_worst_station_from_data(samples)


def get_worst_station_in_route(req):
    return HttpResponse(json.dumps(get_worst_station_in_route_helper(req)))


def get_dates_range(samples):
    dates = [sample[0].actual_departure for sample in samples if sample[0].actual_departure != None]
    return {
        'first': min(dates).isoformat(),
        'last': max(dates).isoformat()
    }


def get_route(req):
    samples = get_relevant_routes_from_request(req)
    if len(samples) == 0:
        return json_resp({'total': 0})

    res = get_delay_from_data(samples)
    res['delay_2'] = get_delay_over_threshold_from_data(samples, 2 * 60)
    res['delay_5'] = get_delay_over_threshold_from_data(samples, 5 * 60)
    res['total'] = len(samples)
    res['dates'] = get_dates_range(samples)
    return json_resp(res)


def get_routes_from_db():
    from django.db import connection

    with connection.cursor() as c:
        c.execute(
            "select stop_ids,count(*) as num_stops from data_trip where valid group by stop_ids order by num_stops DESC")
        routes = c.fetchall()
        return routes


def get_all_routes(req):
    import services

    t1 = time.time()
    routes = list(Route.objects.all())
    if settings.DEBUG:
        print django.db.connection.queries[-1]
        t2 = time.time()
        print 't2 - t1 = %s' % (t2 - t1)
    result = []
    for r in routes:
        stop_ids = r.stop_ids
        count = r.trip_set.count()
        stops = [services.get_stop(sid) for sid in stop_ids]
        result.append(
            {'stops': stops,
             'count': count}
        )
    return json_resp(result)


import time

import django.db


def fill_stop_info(stop, stop_ids):
    t3 = time.time()
    samples = list(Sample.objects.filter(stop_ids=stop_ids,
                                         stop_id=stop['gtfs_stop_id'],
                                         valid=True).values('delay_arrival', 'delay_departure'))
    # print django.db.connection.queries[-1]
    #print len(samples)
    t4 = time.time()
    print 't4 - t3 = %.3f' % (t4 - t3)
    samples_len = float(len(samples))
    stop['avg_delay_arrival'] = sum(x['delay_arrival'] or 0.0 for x in samples) / samples_len
    stop['avg_delay_departure'] = sum(x['delay_departure'] or 0.0 for x in samples) / samples_len
    stop['delay_arrival_gte2'] = sum(1 if x['delay_arrival'] >= 120 else 0 for x in samples) / samples_len
    stop['delay_arrival_gte5'] = sum(1 if x['delay_arrival'] >= 300 else 0 for x in samples) / samples_len
    t5 = time.time()
    print 't5 - t4 = %.3f' % (t5 - t4)


import threading


def get_route_info(req):
    import services

    t1 = time.time()
    stop_ids = [int(s) for s in req.GET['stop_ids'].split(',')]
    trips_len = Trip.objects.filter(stop_ids=stop_ids).count()
    stops = [services.get_stop(sid) for sid in stop_ids]
    t2 = time.time()
    print 't2 - t1 = %.3f' % (t2 - t1)
    use_threads = False  # True
    if use_threads:
        threads = []
        for stop in stops:
            t = threading.Thread(target=fill_stop_info, args=(stop, stop_ids))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
    else:
        for stop in stops:
            fill_stop_info(stop, stop_ids)

    result = {
        'count': trips_len,
        'stops': stops,
    }
    t3 = time.time()
    return json_resp(result)


def contains_stops(route, stop_ids):
    route_stop_ids = route.stop_ids
    try:
        first_index = route_stop_ids.index(stop_ids[0])
    except ValueError:
        return False
    return route_stop_ids[first_index:len(stop_ids) + first_index] == stop_ids


def find_all_routes_with_stops(stop_ids):
    routes = Route.objects.all()
    result = [r for r in routes if contains_stops(r, stop_ids)]
    return result


WEEK_DAYS = [1, 2, 3, 4, 5, 6, 7]
HOURS = [(4, 7),
         (7, 9),
         (9, 12),
         (12, 15),
         (15, 18),
         (18, 21),
         (21, 24),
         (24, 28),
]


def _check_hours():
    for idx, (h1, h2) in enumerate(HOURS):
        assert isinstance(h1, int)
        assert isinstance(h2, int)
        if idx > 0:
            assert h1 == HOURS[idx - 1][1]


_check_hours()


def get_path_info(req):
    stop_ids = [int(s) for s in req.GET['stop_ids'].split(',')]
    routes = find_all_routes_with_stops(stop_ids)
    trips = []
    for r in routes:
        trips.extend(list(r.trip_set.filter(valid=True)))
    stat = _get_path_info_partial(stop_ids,
                                  routes=routes,
                                  trips=trips,
                                  week_day='all',
                                  hours='all')

    return json_resp(stat['stops'])


def get_path_info_full(req):
    stop_ids = [int(s) for s in req.GET['stop_ids'].split(',')]
    # find all routes whose contains these stop ids
    routes = find_all_routes_with_stops(stop_ids)
    trips = []
    for r in routes:
        trips.extend(list(r.trip_set.filter(valid=True)))

    stats = []
    for week_day in WEEK_DAYS + ['all']:
        for hours in HOURS + ['all']:
            stat = _get_path_info_partial(stop_ids,
                                          routes=routes,
                                          all_trips=trips,
                                          week_day=week_day,
                                          hours=hours)
            stats.append(stat)

    return json_resp(stats)


def _get_path_info_partial(stop_ids, routes, all_trips, week_day, hours):
    assert 1 <= week_day <= 7 or week_day == 'all'
    early_threshold = -120
    late_threshold = 300
    all_trip_ids = [trip.id for trip in all_trips]
    if week_day != 'all':
        trips = Trip.objects.filter(id__in=all_trip_ids, start_date__week_day=week_day)
    else:
        trips = all_trips
    trip_ids = [t.id for t in trips]
    cursor = django.db.connection.cursor();
    first_stop_id = stop_ids[0]
    if hours != 'all':
        # find the trips that the first stop_id ***exp*** departure in between the hours range ***
        qs = Sample.objects.filter(trip_id__in=trip_ids,
                                   stop_id=first_stop_id)
        hour_or_query = None
        for hour in range(*hours):
            new_query = Q(exp_departure__hour=(hour%24))
            if hour_or_query is None:
                hour_or_query = new_query
            else:
                hour_or_query = hour_or_query | new_query
        qs = qs.filter(hour_or_query)
        trip_ids = list(qs.values_list('trip_id',flat=True))
        trips = [t for t in  trips if t.id in trip_ids]

    cursor.execute('''
        SELECT  s.stop_id as stop_id,
                avg(case when delay_arrival <= %(early_threshold)s then 1.0 else 0.0 end)::float as arrival_early_pct,
                avg(case when delay_arrival > %(early_threshold)s and delay_arrival < %(late_threshold)s then 1.0 else 0.0 end)::float as arrival_on_time_pct,
                avg(case when delay_arrival >= %(late_threshold)s then 1.0 else 0.0 end)::float as arrival_late_pct,

                avg(case when delay_departure <= %(early_threshold)s then 1.0 else 0.0 end)::float as departure_early_pct,
                avg(case when delay_departure > %(early_threshold)s and delay_departure < %(late_threshold)s then 1.0 else 0.0 end)::float as departure_on_time_pct,
                avg(case when delay_departure >= %(late_threshold)s then 1.0 else 0.0 end)::float as departure_late_pct

        FROM    data_sample as s
        WHERE   s.stop_id = ANY (%(stop_ids)s)
        AND     s.valid
        AND     s.trip_id = ANY (%(trip_ids)s)
        GROUP BY s.stop_id
    ''', {
        'early_threshold': early_threshold,
        'late_threshold': late_threshold,
        'stop_ids': stop_ids,
        'trip_ids': trip_ids
    })

    cols = [
        'stop_id',
        'arrival_early_pct', 'arrival_on_time_pct', 'arrival_late_pct',
        'departure_early_pct', 'departure_on_time_pct', 'departure_late_pct'
    ]
    stats_map = {}
    for row in cursor:
        stat = dict(zip(cols, row))
        stats_map[stat['stop_id']] = stat
    return {
        'info': {
            'num_trips': len(trips),
            'week_day': week_day,
            'hours': hours,
        },
        'stops': list(stats_map.get(stop_id,{}) for stop_id in stop_ids)
    }


