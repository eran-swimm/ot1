from . import chat_step
from chatbot.station_utils import StationUtils
from chatbot.chat_utils import ChatUtils


class SourceStationStep(chat_step.ChatStep):
    @staticmethod
    def get_name():
        return 'source_station'

    def send_message(self):
        previous_response = ChatUtils.get_response_to_step(self.session, self.get_name())
        if previous_response:
            text = self._extract_text(previous_response)
            matching_stations = StationUtils.find_matching_stations(text)
            if 2 <= len(matching_stations) <= self.MAX_ITEMS_FOR_SUGGESTIONS:
                message = 'איזו מאלה?'
                suggestions = []
                for station in matching_stations:
                    suggestions.append({
                        'text': station.main_name,
                        'payload': station.id,
                    })
                self._send_suggestions(message, suggestions)
                return

            self._send_message('אני לא כל כך בטוח איזו תחנה זו, אולי ננסה משהו יותר ספציפי?')
            return

        self._send_message('מאיזו תחנה?')

    def handle_user_response(self, messaging_event):
        if self._is_quick_reply(messaging_event):
            station_id = self._extract_selected_quick_reply(messaging_event)
            matching_station = StationUtils.get_station_by_id(station_id=station_id)
            matching_stations = [matching_station] if matching_station else []
        else:
            text = self._extract_text(messaging_event)
            matching_stations = StationUtils.find_matching_stations(text)

        if len(matching_stations) == 0:
            self._send_message('האמת שאני לא מכיר תחנה כזאת...')
            return self.get_name()

        if 2 <= len(matching_stations) <= self.MAX_ITEMS_FOR_SUGGESTIONS:
            return self.get_name()

        if len(matching_stations) > self.MAX_ITEMS_FOR_SUGGESTIONS:
            self._send_message('אני לא כל כך בטוח איזו תחנה זו, אולי ננסה משהו יותר ספציפי?')
            return self.get_name()

        station = matching_stations[0]
        station_name = station.main_name
        self._set_step_data(station.gtfs_code)
        self._send_message(station_name + ' 👍')
        return 'destination_station'
