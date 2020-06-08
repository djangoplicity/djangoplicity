from djangoplicity.utils import datetimes

class TestDatetimes:
    def test_timestring_to_seconds(self):
        """ test correct conversion of H:m:s:f to seconds """
        time = '10:30:40:0'
        seconds = (10 * 60 * 60) + (30 * 60) + 40
        
        calculated_seconds = datetimes.timestring_to_seconds(time)
        assert seconds == calculated_seconds