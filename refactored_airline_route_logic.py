# Refactored Airline Route Logic - Python Translation
# Original script: https://raw.githubusercontent.com/centralkindomMiChen/AirlineRouteTypeAutoSort/main/omRouteType%E8%B0%83%E8%AF%95%E9%98%B6%E6%AE%B5%E4%BB%A3%E7%A0%812.js

import re

# Global constant for city to region mappings
CITY_REGION_MAPPINGS = [
    ["AE", "AsianPacific"], ["AF", "AsianPacific"], ["AR", "Americas"],
    ["AT", "Europe"], ["AU", "Australia"], ["AZ", "AsianPacific"],
    ["BA", "Europe"], ["BE", "Europe"], ["BG", "Europe"],
    ["BH", "AsianPacific"], ["BJ", "Africa"], ["BR", "Europe"], # Note: BR is listed as Europe, might be an error in original data
    ["CA", "Americas"], ["CH", "Europe"], ["CN", "AsianPacific"],
    ["CU", "Americas"], ["CZ", "Europe"], ["DE", "Europe"],
    ["DK", "Europe"], ["ES", "Europe"], ["ET", "Africa"],
    ["FI", "Europe"], ["FR", "Europe"], ["GB", "Europe"],
    ["GR", "Europe"], ["HK", "Region"], ["HU", "Europe"],
    ["ID", "AsianPacific"], ["IL", "AsianPacific"], ["IN", "AsianPacific"],
    ["IR", "AsianPacific"], ["IT", "Europe"], ["JP", "AsianPacific"],
    ["KH", "AsianPacific"], ["KR", "AsianPacific"], ["LU", "Europe"],
    ["MM", "AsianPacific"], ["MN", "AsianPacific"], ["MO", "Region"],
    ["MX", "Americas"], ["MY", "AsianPacific"], ["NL", "Europe"],
    ["NO", "Europe"], ["NP", "AsianPacific"], ["NZ", "Australia"],
    ["OM", "AsianPacific"], ["PA", "Americas"], ["PH", "AsianPacific"],
    ["PK", "AsianPacific"], ["PL", "Europe"], ["PT", "Europe"],
    ["RO", "Europe"], ["RU", "Europe"], ["SE", "Europe"],
    ["SG", "AsianPacific"], ["SK", "Europe"], ["TH", "AsianPacific"],
    ["TR", "Europe"], ["TW", "Region"], ["UG", "Africa"],
    ["US", "Americas"], ["VN", "AsianPacific"], ["ZA", "Africa"],
    ["/", "/"] # Represents a separator or unknown
]

# Simulating a global data layer object for analytics
data_xayer = {}
omcountry = None # Global variable used in original JS, ensure it's available if needed by direct logic copy

# Regex patterns compiled for efficiency
MULTI_CITY_REGEX_PATTERN = r"^(CA\d{4}\-\/\-)+(CA\d{4}\-)+(CA\d{3}\-)+\/(\-CA\d{4})+$|^(CA\d{4}\-\/\-)+(CA\d{4}\-)+(CA\d{3}\-)+\/(\-CA\d{3})+$|^(CA\d{4}\-\/\-)+(CA\d{3}\-\/\-)+CA\d{4}$|^(CA\d{4}\-\/\-)+(CA\d{3}\-\/\-)+CA\d{3}$|^(CA\d{4}\-\/\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{4})+$|^(CA\d{4}\-\/\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+\-\/(\-CA\d{4})+$|^(CA\d{4}\-\/\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+$|^(CA\d{4}\-)+\/(\-CA\d{4})*(\-CA\d{3})+\-\/(\-CA\d{3})+(\-CA\d{4})*$|^(CA\d{4}\-)+(CA\d{3}\-)+\/\-(CA\d{4}\-)*(CA\d{3}\-)*\/(\-CA\d{4})+$|^(CA\d{3}\-\/\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{4})+$|^(CA\d{4}\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+(\-CA\d{4})+$|^(CA\d{4}\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+(\-CA\d{4})*$|^(CA\d{4}\-)*(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+(\-CA\d{4})+$|^(CA\d{4}\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{3})*(\-CA\d{4})+$|^(CA\d{4}\-)+\/\-(CA\d{4}\-\/\-)+(CA\d{3}\-\/\-)+(CA\d{3}\-)*(CA\d{4}\-)*(CA\d{4})*$|^(\w{2}\d{4}\-(.+)?\-)+(\w{2}\d{3,4}\-)+(.+)?(.+)?(\w{2}\d{3,4}\-)+(.+)?(.+)?(\-?\w{2}\d{3,4}\-\/?)+(\-?\w{2}\d{4})+$|^(\w{2}\d{4}\-(.+)?(.+)?)+(\-\w{2}\d{3})+$"
ROUND_TRIP_REGEX_PATTERN = r"^(\w{2}\d{4}\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+(\-\w{2}\d{4})+$|^(\w{2}\d{4}\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+(\-\w{2}\d{4})*$|^(\w{2}\d{4}\-)*(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+(\-\w{2}\d{4})+$"
ONE_WAY_REGEX_PATTERN = r"^\w{2}\d{4}\-CA\d{3}$"

AIR_CHINA_CODESHARE_REGEX_PATTERN = r"CA[7][0123456][\d][\d]|CA[6][102456789][\d][\d]|CA[5][2325641960][\d][\d]"
SIMPLE_FLIGHT_FORMAT_REGEX_PATTERN = r"^\w{2}\d+$"
ROUND_TRIP_FLIGHT_FORMAT_REGEX_PATTERN = r"^\w{2}\d+-\/-\w{2}\d+$"
IET_FLIGHT_REGEX_PATTERN = r"^([\w/-]+-)*(((?!CA\d).)+?\d+([A-Z])?-?)+([\w/-]+-?)*$"
RAIL_CODE_REGEX_PATTERN = r"9B"
FIFTH_FREEDOM_REGEX_PATTERN = r"ES-BR|BR-ES|CA-CU|CU-CA|US-PA|PA-US|HU-BY|BY-HU"
INTERNATIONAL_TO_INTERNATIONAL_REGEX_PATTERN = r"^((?!CN).{2})-((?!CN).{2})$"
CHINA_TO_INTERNATIONAL_REGEX_PATTERN = r"^(CN-((?!CN).{2})|((?!CN).{2})-CN)$"
INTERNATIONAL_VIA_CHINA_REGEX_PATTERN = r"^((?!CN).{2})-CN-((?!CN).{2})"


def is_multi_city_route(route_string):
    if not route_string: return False
    # Test with just the first branch of the regex if the full one causes issues.
    # first_branch_multi_city = r"^(CA\d{4}\-\/\-)+(CA\d{4}\-)+(CA\d{3}\-)+\/(\-CA\d{4})+$"
    # return bool(re.search(first_branch_multi_city, route_string, re.IGNORECASE))
    return bool(re.search(MULTI_CITY_REGEX_PATTERN, route_string, re.IGNORECASE))

def is_valid_round_trip_route_format(route_string):
    if not route_string: return False
    return bool(re.search(ROUND_TRIP_REGEX_PATTERN, route_string, re.IGNORECASE))

def is_valid_one_way_route_format(route_string):
    if not route_string: return False
    return bool(re.search(ONE_WAY_REGEX_PATTERN, route_string, re.IGNORECASE))

def get_regions_for_itinerary(itinerary_string):
    if not itinerary_string: return ""
    parts = itinerary_string.split('-')
    regions = []
    for part in parts:
        # Skip empty strings that arise from patterns like "-/-"
        if not part: 
            continue 
        
        found_region = None
        for mapping in CITY_REGION_MAPPINGS:
            if part == mapping[0]: # part could be "CN", "DE", or even "/" if it's a mapped code
                found_region = mapping[1]
                break
        if found_region:
            regions.append(found_region)
        else: 
            # If part is "/" but not in mapping (e.g. mapping removed), it would become UnknownRegion here.
            # However, current mapping has ["/", "/"], so "/" is a found_region.
            regions.append("UnknownRegion")
    return "-".join(regions)


def get_region_for_city(city_or_country_code): 
    if not city_or_country_code: return None
    for mapping in CITY_REGION_MAPPINGS:
        if city_or_country_code == mapping[0]:
            return mapping[1]
    return None

def extract_product_data(data_type):
    products_string = data_xayer.get("products")
    if not products_string or not isinstance(products_string, str): return ""
    
    parts = products_string.split(':')
    
    route_type_abbrev = ""
    
    if products_string.startswith(";"):
        if not parts or len(parts[0]) <= 1: return "" 
        route_type_abbrev = parts[0][1:] 
        # Min parts for ";TYPE:OD:ITIN:CABIN..." is 4 (parts[0] to parts[3])
        # e.g. parts = [";MC", "NRT-SIN", "NRT-HKG-SIN", "Y"] -> len is 4
        if len(parts) < 4: return "" 
        origin_destination_string = parts[1]
        whole_itinerary_indicator = parts[2]
        cabin_class_part_full = parts[3] 
    else:
        if not parts: return "" 
        route_type_abbrev = parts[0] 
        # Min parts for "TYPE:OD:ITIN:CABIN..." is 4
        if len(parts) < 4: return ""
        origin_destination_string = parts[1]
        whole_itinerary_indicator = parts[2]
        cabin_class_part_full = parts[3]

    if not route_type_abbrev: return "" 

    if not origin_destination_string or len(origin_destination_string) < 7 or '-' not in origin_destination_string:
        return "" 
    
    origin_city = origin_destination_string[0:3]
    destination_city = origin_destination_string[4:7] 
    
    cabin_class = cabin_class_part_full[0] if cabin_class_part_full else "x" 
    if not cabin_class_part_full: 
        cabin_class = "x"

    route_type_with_cabin = route_type_abbrev + ":" + cabin_class

    if data_type == "a": return route_type_with_cabin
    if data_type == "b": return origin_city
    if data_type == "c": return destination_city
    if data_type == "d": return whole_itinerary_indicator
    return ""

def get_unique_array_elements_excluding_slash(array_with_duplicates):
    if not array_with_duplicates or not isinstance(array_with_duplicates, list): return []
    seen = set()
    unique_list = []
    for item in array_with_duplicates:
        if item != "/" and item not in seen:
            seen.add(item)
            unique_list.append(item)
    return unique_list
    
def get_unique_array_elements(array_with_duplicates):
    if not array_with_duplicates or not isinstance(array_with_duplicates, list): return []
    seen = set()
    unique_list = []
    for item in array_with_duplicates:
        if item not in seen:
            seen.add(item)
            unique_list.append(item)
    return unique_list

def count_regex_matches(regex_pattern, search_string):
    if search_string is None or not regex_pattern: return 0
    return len(re.findall(regex_pattern, search_string, re.IGNORECASE))

def check_for_taopiao(itinerary_city_string):
    if not isinstance(itinerary_city_string, str): return None
    segments = itinerary_city_string.split("/")
    outbound_segment_parts = []
    inbound_segment_parts = []
    for i, segment in enumerate(segments):
        cleaned_segment = re.sub(r"\-+", "", segment)
        if i % 2 == 0:
            outbound_segment_parts.append(cleaned_segment)
        else:
            inbound_segment_parts.append(cleaned_segment)
    
    unique_outbound_identifiers = get_unique_array_elements(outbound_segment_parts)
    unique_inbound_identifiers = get_unique_array_elements(inbound_segment_parts)

    if len(unique_outbound_identifiers) == 1 and len(unique_inbound_identifiers) == 1:
        outbound_id = unique_outbound_identifiers[0]
        inbound_id = unique_inbound_identifiers[0]
        combined_identifier = outbound_id + ":" + inbound_id
        correct_taopiao_regex = r"^(\w{3})(\w{3}):\2\1$"
        if re.search(correct_taopiao_regex, combined_identifier, re.IGNORECASE):
            return "taopiao"
    return None

def get_international_route_type(itinerary_country_segment):
    if re.search(FIFTH_FREEDOM_REGEX_PATTERN, itinerary_country_segment, re.IGNORECASE):
        return "5thFreedom"
    return "I+I/6thFreedom"

def get_china_international_route_type(flight_numbers, origin_direct_country, is_round_trip_behavior, aircraft_types, data_xayer_om_country, route_input_string_for_regex_fn):
    global omcountry 
    effective_om_country = data_xayer_om_country if data_xayer_om_country is not None else omcountry

    if not flight_numbers and not route_input_string_for_regex_fn: return "PtoP/ConnectingFlights"
    testable_flight_string = route_input_string_for_regex_fn or flight_numbers

    if origin_direct_country == "CN":
        if (is_round_trip_behavior and is_valid_round_trip_route_format(testable_flight_string)) or \
           (not is_round_trip_behavior and (is_valid_one_way_route_format(testable_flight_string) or is_multi_city_route(testable_flight_string))):
            return "D+I"

    if (is_round_trip_behavior and re.search(ROUND_TRIP_FLIGHT_FORMAT_REGEX_PATTERN, testable_flight_string, re.IGNORECASE)) or \
       (not is_round_trip_behavior and re.search(SIMPLE_FLIGHT_FORMAT_REGEX_PATTERN, testable_flight_string, re.IGNORECASE)):
        if re.search(AIR_CHINA_CODESHARE_REGEX_PATTERN, testable_flight_string, re.IGNORECASE):
            return "PointToPoint(codeShare)"
        return "PointToPoint"
    
    if re.search(IET_FLIGHT_REGEX_PATTERN, testable_flight_string, re.IGNORECASE):
        if re.search(RAIL_CODE_REGEX_PATTERN, testable_flight_string, re.IGNORECASE):
            if effective_om_country == "DE": return "DBrailway"
            if effective_om_country == "IT" and aircraft_types and "ITRail" in aircraft_types: return "ITrailway"
        if origin_direct_country == "CN":
            return "D+I" 
        return "IET"

    if re.search(AIR_CHINA_CODESHARE_REGEX_PATTERN, testable_flight_string, re.IGNORECASE):
        return "CodeShare(OverSeas)"

    return "D+I" if origin_direct_country == "CN" else "I+D"

def determine_route_type_rtow(route_input_string):
    global data_xayer 
    if not route_input_string or not isinstance(route_input_string, str): return None
    parts = route_input_string.split(':')
    if len(parts) < 4: return "Others"
    
    route_category = parts[0]
    direct_od_countries = parts[2]
    whole_itinerary_by_country = parts[3]
    
    if route_category == "MC": return None
    
    origin_direct_country = direct_od_countries[0:2]
    unique_countries_in_itinerary = "".join(get_unique_array_elements_excluding_slash(whole_itinerary_by_country.split('-')))
    
    if unique_countries_in_itinerary == "CN": return "pureDOM" 

    flight_numbers = data_xayer.get("wholefltNbr")
    aircraft_types = data_xayer.get("aircftTp")
    current_om_country = data_xayer.get("omcountry", data_xayer.get("depCountry"))


    if route_category == "OW":
        if re.search(INTERNATIONAL_TO_INTERNATIONAL_REGEX_PATTERN, whole_itinerary_by_country, re.IGNORECASE):
            return get_international_route_type(whole_itinerary_by_country)
        elif re.search(CHINA_TO_INTERNATIONAL_REGEX_PATTERN, whole_itinerary_by_country, re.IGNORECASE):
            return get_china_international_route_type(flight_numbers, origin_direct_country, False, aircraft_types, current_om_country, flight_numbers)
    elif route_category == "RT":
        if re.search(INTERNATIONAL_TO_INTERNATIONAL_REGEX_PATTERN, direct_od_countries, re.IGNORECASE):
            return get_international_route_type(direct_od_countries)
        elif re.search(CHINA_TO_INTERNATIONAL_REGEX_PATTERN, direct_od_countries, re.IGNORECASE):
            return get_china_international_route_type(flight_numbers, origin_direct_country, True, aircraft_types, current_om_country, flight_numbers)
            
    return "Others"

def determine_route_type_mc(route_input_string):
    global data_xayer 
    if not route_input_string or not isinstance(route_input_string, str): return None
    parts = route_input_string.split(':')
    if len(parts) < 4: return "ConnectingFlights(MultiCity)"
    
    route_category = parts[0]
    direct_od_countries = parts[2]
    whole_itinerary_by_country = parts[3]

    if route_category != "MC": return None

    products_string = data_xayer.get("products")
    whole_itinerary_cities = data_xayer.get("wholeIti")
    flight_numbers = data_xayer.get("wholefltNbr")
    aircraft_types = data_xayer.get("aircftTp")
    current_om_country = data_xayer.get("omcountry", data_xayer.get("depCountry"))


    if not all([products_string, whole_itinerary_cities, flight_numbers]):
        return "ConnectingFlights(MultiCity)"

    overall_origin_city = extract_product_data("b")
    overall_destination_city = extract_product_data("c")
    first_city_in_itinerary = whole_itinerary_cities[0:3]
    last_city_in_itinerary = whole_itinerary_cities[-3:]
    
    unique_countries_in_itinerary = get_unique_array_elements_excluding_slash(whole_itinerary_by_country.split('-'))
    unique_countries_string = "".join(unique_countries_in_itinerary)
    origin_direct_country = direct_od_countries[0:2]

    is_taopiao = check_for_taopiao(whole_itinerary_cities)
    if is_taopiao == "taopiao": return "TAOPIAO"
    if unique_countries_string == "CN": return "pureDOM"

    open_jaw_type = ""
    city_itinerary_segments = whole_itinerary_cities.split('/-')
    if len(city_itinerary_segments) > 1:
        first_leg_destination_city = city_itinerary_segments[0][-3:]
        second_leg_origin_city = city_itinerary_segments[1][0:3]
        if first_leg_destination_city != second_leg_origin_city:
            open_jaw_type = "OpenJaw(TurnaroundOJ)"
    
    if overall_origin_city != first_city_in_itinerary or overall_destination_city != last_city_in_itinerary:
        open_jaw_type = "OpenJaw(DoubleOJ)" if open_jaw_type == "OpenJaw(TurnaroundOJ)" else "OpenJaw(OriginOJ)"

    if open_jaw_type:
        is_railway_iet = bool(re.search(RAIL_CODE_REGEX_PATTERN, flight_numbers, re.IGNORECASE) and \
                           (current_om_country == "DE" or (current_om_country == "IT" and aircraft_types and "ITRail" in aircraft_types)))
        if not is_railway_iet:
            return open_jaw_type
    
    if re.search(IET_FLIGHT_REGEX_PATTERN, flight_numbers, re.IGNORECASE):
        if re.search(RAIL_CODE_REGEX_PATTERN, flight_numbers, re.IGNORECASE):
            if current_om_country == "DE": return "DBrailway"
            if current_om_country == "IT" and aircraft_types and "ITRail" in aircraft_types: return "ITrailway"
        
        if len(unique_countries_in_itinerary) >= 3:
            simplified_country_itinerary = whole_itinerary_by_country.replace("/-", "-")
            if re.search(INTERNATIONAL_VIA_CHINA_REGEX_PATTERN, simplified_country_itinerary, re.IGNORECASE) and direct_od_countries != "CN-CN":
                return "I+I/6thFreedom"
        
        if open_jaw_type and (re.search(RAIL_CODE_REGEX_PATTERN, flight_numbers, re.IGNORECASE) and \
                           (current_om_country == "DE" or (current_om_country == "IT" and aircraft_types and "ITRail" in aircraft_types))):
            if current_om_country == "DE": return "DBrailway"
            if current_om_country == "IT" and aircraft_types and "ITRail" in aircraft_types: return "ITrailway"
        return "IET"

    if re.search(AIR_CHINA_CODESHARE_REGEX_PATTERN, flight_numbers, re.IGNORECASE):
        return "CodeShare(OverSeas)"

    if len(unique_countries_in_itinerary) >= 3:
        simplified_country_itinerary = whole_itinerary_by_country.replace("/-", "-")
        if re.search(INTERNATIONAL_VIA_CHINA_REGEX_PATTERN, simplified_country_itinerary, re.IGNORECASE) and direct_od_countries != "CN-CN":
            return "I+I/6thFreedom"
        if count_regex_matches("CN", whole_itinerary_by_country) == 0 and direct_od_countries != "CN-CN":
            return "I+I/6thFreedom"
            
    elif len(unique_countries_in_itinerary) == 2:
        fifth_freedom_test_string = unique_countries_string.replace("CN", "")
        if len(fifth_freedom_test_string) == 4: 
            test_pair = fifth_freedom_test_string[0:2] + "-" + fifth_freedom_test_string[2:4]
            if get_international_route_type(test_pair) == "5thFreedom":
                return "5thFreedom"
        if count_regex_matches("CN", unique_countries_string) == 0: 
            return "I+I/6thFreedom"

    if count_regex_matches("CN", whole_itinerary_by_country) >= 1:
        if is_multi_city_route(flight_numbers):
            return "D+I" if origin_direct_country == "CN" else "I+D"
            
    if open_jaw_type: return open_jaw_type
    
    return "ConnectingFlights(MultiCity)"


def run_debug():
    global data_xayer, omcountry 
    print("--- Starting Debug Run ---")
    
    test_cases = [
        {
            "name": "Round Trip (US-CN)",
            "data": {
                "routeType": "RT", "cabin": "E", "depandArrCountry": "US-CN",
                "wholeitibyCountry": "US-CN-/-CN-US", "aircftTp": "777:330",
                "wholefltNbr": "CA986-/-CA985", "products": ";RT:SFO-PEK:SFO-PEK-/-PEK-SFO:E:Ad",
                "depCountry": "US", "arrCountry": "CN", "wholeIti": "SFO-PEK-/-PEK-SFO"
            }
        },
        {
            "name": "Multi-City (US-CN-JP)",
            "data": {
                "routeType": "MC", "cabin": "Y", "depandArrCountry": "US-JP",
                "wholeitibyCountry": "US-CN-JP", "wholefltNbr": "UA123-CA456-JL789",
                "products": ";MC:LAX-NRT:LAX-PEK-NRT:Y:Ad", "depCountry": "US",
                "arrCountry": "JP", "wholeIti": "LAX-PEK-NRT"
            }
        },
        {
            "name": "Pure Domestic OW (CN-CN)",
            "data": {
                "routeType": "OW", "cabin": "Y", "depandArrCountry": "CN-CN",
                "wholeitibyCountry": "CN-CN", "wholefltNbr": "CA1832",
                "products": ";OW:PEK-SHA:PEK-SHA:Y:Ad", "depCountry": "CN",
                "arrCountry": "CN", "wholeIti": "PEK-SHA"
            }
        },
        {
            "name": "Intl to Intl RT (DE-FR)",
            "data": {
                "routeType": "RT", "cabin": "C", "depandArrCountry": "DE-FR",
                "wholeitibyCountry": "DE-FR-/-FR-DE", "wholefltNbr": "LH100-/-LH101",
                "products": ";RT:FRA-CDG:FRA-CDG-/-CDG-FRA:C:Ad", "depCountry": "DE",
                "arrCountry": "FR", "wholeIti": "FRA-CDG-/-CDG-FRA"
            }
        },
        {
            "name": "Fifth Freedom OW (ES-BR)",
            "data": {
                "routeType": "OW", "cabin": "Y", "depandArrCountry": "ES-BR",
                "wholeitibyCountry": "ES-BR", "wholefltNbr": "IB6827",
                "products": ";OW:MAD-GRU:MAD-GRU:Y:Ad", "depCountry": "ES",
                "arrCountry": "BR", "wholeIti": "MAD-GRU"
            }
        },
        {
            "name": "D+I OW (CN-US)",
            "data": {
                "routeType": "OW", "cabin": "Y", "depandArrCountry": "CN-US",
                "wholeitibyCountry": "CN-US", "wholefltNbr": "XY1234-CA789",
                "products": ";OW:PEK-JFK:PEK-JFK:Y:Ad", "depCountry": "CN",
                "arrCountry": "US", "wholeIti": "PEK-JFK"
            }
        },
        {
            "name": "TAOPIAO MC",
            "data": {
                "routeType": "MC", "cabin": "Y", "depandArrCountry": "CN-CN",
                "wholeitibyCountry": "CN-CN-/-CN-CN", "wholefltNbr": "CA101/CA102",
                "products": ";MC:PEK-PEK:PEK-SHA-/-SHA-PEK:Y:Ad", "depCountry": "CN",
                "arrCountry": "CN", "wholeIti": "PEK-SHA-/-SHA-PEK"
            }
        },
        {
            "name": "OpenJaw (OriginOJ) MC", 
            "data": {
                "routeType": "MC", "cabin": "C", "depandArrCountry": "US-CA",
                "wholeitibyCountry": "US-CA-/-CA-CA", "wholefltNbr": "UA500/AC100-AC102",
                "products": ";MC:SFO-YYZ:SFO-YVR-/-YUL-YYZ:C:Ad", "depCountry": "US",
                "arrCountry": "CA", "wholeIti": "SFO-YVR-/-YUL-YYZ"
            }
        }
    ]

    for test_case_info in test_cases:
        print(f"--- Test Case: {test_case_info['name']} ---")
        data_xayer = test_case_info["data"].copy() 
        omcountry = data_xayer.get("depCountry") 

        route_input_string = f"{data_xayer['routeType']}:{data_xayer['cabin']}:{data_xayer['depandArrCountry']}:{data_xayer['wholeitibyCountry']}"
        
        result = None
        if data_xayer['routeType'] in ["RT", "OW"]:
            result = determine_route_type_rtow(route_input_string)
            print(f"Input for RTOW: {route_input_string}")
        elif data_xayer['routeType'] == "MC":
            result = determine_route_type_mc(route_input_string)
            print(f"Input for MC: {route_input_string}")
        
        print(f"Calculated Route Type: {result}")
        print("--- End Test Case ---")
        
    print("--- Debug Run Finished ---")

if __name__ == '__main__':
    run_debug()
