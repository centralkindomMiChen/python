// Refactored Airline Route Logic
// Original script: https://raw.githubusercontent.com/centralkindomMiChen/AirlineRouteTypeAutoSort/main/omRouteType%E8%B0%83%E8%AF%95%E9%98%B6%E6%AE%B5%E4%BB%A3%E7%A0%812.js

// Global constant for city to region mappings
const CITY_REGION_MAPPINGS = [
    ["AE", "AsianPacific"], ["AF", "AsianPacific"], ["AR", "Americas"],
    ["AT", "Europe"], ["AU", "Australia"], ["AZ", "AsianPacific"],
    ["BA", "Europe"], ["BE", "Europe"], ["BG", "Europe"],
    ["BH", "AsianPacific"], ["BJ", "Africa"], ["BR", "Europe"], // Note: BR is listed as Europe, might be an error in original data
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
    ["/", "/"] // Represents a separator or unknown
];

// Simulating a global data layer object for analytics
var dataXayer = {}; 

function isMultiCityRoute(routeString) {
    const multiCityRegex = /^(CA\d{4}\-\/\-)+(CA\d{4}\-)+(CA\d{3}\-)+\/(\-CA\d{4})+$|^(CA\d{4}\-\/\-)+(CA\d{4}\-)+(CA\d{3}\-)+\/(\-CA\d{3})+$|^(CA\d{4}\-\/\-)+(CA\d{3}\-\/\-)+CA\d{4}$|^(CA\d{4}\-\/\-)+(CA\d{3}\-\/\-)+CA\d{3}$|^(CA\d{4}\-\/\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{4})+$|^(CA\d{4}\-\/\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+\-\/(\-CA\d{4})+$|^(CA\d{4}\-\/\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+$|^(CA\d{4}\-)+\/(\-CA\d{4})*(\-CA\d{3})+\-\/(\-CA\d{3})+(\-CA\d{4})*$|^(CA\d{4}\-)+(CA\d{3}\-)+\/\-(CA\d{4}\-)*(CA\d{3}\-)*\/(\-CA\d{4})+$|^(CA\d{3}\-\/\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{4})+$|^(CA\d{4}\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+(\-CA\d{4})+$|^(CA\d{4}\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+(\-CA\d{4})*$|^(CA\d{4}\-)*(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+(\-CA\d{4})+$|^(CA\d{4}\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{3})*(\-CA\d{4})+$|^(CA\d{4}\-)+\/\-(CA\d{4}\-\/\-)+(CA\d{3}\-\/\-)+(CA\d{3}\-)*(CA\d{4}\-)*(CA\d{4})*$|^(\w{2}\d{4}\-(.+)?\-)+(\w{2}\d{3,4}\-)+(.+)?(.+)?(\w{2}\d{3,4}\-)+(.+)?(.+)?(\-?\w{2}\d{3,4}\-\/?)+(\-?\w{2}\d{4})+$|^(\w{2}\d{4}\-(.+)?(.+)?)+(\-\w{2}\d{3})+$/ig;
    if (!routeString) return false;
    return multiCityRegex.test(routeString);
}

function isValidRoundTripRouteFormat(routeString) {
    const roundTripRegex = /^(\w{2}\d{4}\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+(\-\w{2}\d{4})+$|^(\w{2}\d{4}\-)+(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+(\-\w{2}\d{4})*$|^(\w{2}\d{4}\-)*(CA\d{3}\-)+(CA\d{4}\-)*\/(\-CA\d{4})*(\-CA\d{3})+(\-\w{2}\d{4})+$/ig;
    if (!routeString) return false;
    return roundTripRegex.test(routeString);
}

function isValidOneWayRouteFormat(routeString) {
    const oneWayRegex = /^\w{2}\d{4}\-CA\d{3}$/ig;
    if (!routeString) return false;
    return oneWayRegex.test(routeString);
}

function getRegionsForItinerary(itineraryString) {
    if (!itineraryString) return "";
    const cityCodes = itineraryString.split("-");
    const regions = [];
    for (const cityCode of cityCodes) {
        let foundRegion = null;
        for (const mapping of CITY_REGION_MAPPINGS) {
            if (cityCode === mapping[0]) {
                foundRegion = mapping[1];
                break; 
            }
        }
        if (foundRegion) regions.push(foundRegion);
        else if (cityCode !== "/") regions.push("UnknownRegion");
    }
    return regions.join("-");
}

function getRegionForCity(cityCode) {
    if (!cityCode) return undefined;
    for (const mapping of CITY_REGION_MAPPINGS) {
        if (cityCode === mapping[0]) return mapping[1];
    }
    return undefined;
}

function extractProductData(dataType) {
    const productsString = dataXayer.products;
    if (!productsString || typeof productsString !== 'string') return "";
    const parts = productsString.split(':');
    // Expects format like ";RT:SFO-PEK:SFO-PEK-/-PEK-SFO:E:Ad"
    // So parts[0] would be ";RT". If no ";", parts[0] is "RT".
    if (parts.length < 4 && parts.length < (productsString.startsWith(";") ? 5 : 4)) return "";
    
    let routeTypeAbbrev = parts[0];
    if (productsString.startsWith(";")) { // If it starts with ";", then parts[0] is like ";RT"
         routeTypeAbbrev = parts[0].substring(1,3); // Get "RT" from ";RT"
    } else { // If it's "RT:...", parts[0] is "RT"
        routeTypeAbbrev = parts[0];
    }
    // If productString was ";RT:SFO-PEK:...", then parts are [";RT", "SFO-PEK", "SFO-PEK-/-PEK-SFO", "E", "Ad"]
    // If productString was "RT:SFO-PEK:...", then parts are ["RT", "SFO-PEK", "SFO-PEK-/-PEK-SFO", "E", "Ad"]
    // Adjust index based on presence of ";" prefix
    const baseIndex = productsString.startsWith(";") ? 0 : -1;

    const originDestinationString = parts[baseIndex + 1]; 
    const wholeItineraryIndicator = parts[baseIndex + 2]; 
    let cabinClass = parts[baseIndex + 3]; 

    if (!originDestinationString || originDestinationString.length < 7 || originDestinationString.indexOf('-') === -1) return "";
    const originCity = originDestinationString.substr(0, 3);
    const destinationCity = originDestinationString.substr(4, 3);
    if (cabinClass === "" || cabinClass === undefined) cabinClass = "x";
    if (cabinClass.length > 1) cabinClass = cabinClass.charAt(0); // E.g., "E" from "E" or "E:Ad"
    const routeTypeWithCabin = routeTypeAbbrev + ":" + cabinClass;

    if (dataType === "a") return routeTypeWithCabin;
    if (dataType === "b") return originCity;
    if (dataType === "c") return destinationCity;
    if (dataType === "d") return wholeItineraryIndicator;
    return "";
}

function getUniqueArrayElementsExcludingSlash(arrayWithDuplicates) {
    if (!arrayWithDuplicates || !Array.isArray(arrayWithDuplicates)) return [];
    const uniqueArray = [];
    for (const item of arrayWithDuplicates) {
        if (uniqueArray.indexOf(item) === -1 && item !== "/") uniqueArray.push(item);
    }
    return uniqueArray;
}

function getUniqueArrayElements(arrayWithDuplicates) {
    if (!arrayWithDuplicates || !Array.isArray(arrayWithDuplicates)) return [];
    const uniqueArray = [];
    for (const item of arrayWithDuplicates) {
        if (uniqueArray.indexOf(item) === -1) uniqueArray.push(item);
    }
    return uniqueArray;
}

function countRegexMatches(regexPattern, searchString) {
    if (searchString === undefined || searchString === null || !regexPattern) return 0;
    const regex = new RegExp(regexPattern, "ig");
    const matches = searchString.match(regex);
    return matches ? matches.length : 0;
}

function checkForTaopiao(itineraryCityString) {
    if (typeof itineraryCityString !== 'string') return undefined;
    const segments = itineraryCityString.split("/");
    const outboundSegmentParts = [];
    const inboundSegmentParts = [];
    for (let i = 0; i < segments.length; i++) {
        if (i % 2 === 0) outboundSegmentParts.push(segments[i].replace(/\-+/ig, ""));
        else inboundSegmentParts.push(segments[i].replace(/\-+/ig, ""));
    }
    const uniqueOutboundIdentifiers = getUniqueArrayElements(outboundSegmentParts);
    const uniqueInboundIdentifiers = getUniqueArrayElements(inboundSegmentParts);
    if (uniqueOutboundIdentifiers.length === 1 && uniqueInboundIdentifiers.length === 1) {
        const outboundID = uniqueOutboundIdentifiers[0];
        const inboundID = uniqueInboundIdentifiers[0];
        const combinedIdentifier = outboundID + ":" + inboundID;
        const correctTaopiaoRegex = /^(\w{3})(\w{3})\:\2\1$/ig; // e.g. PEKSHA:SHAPEK
        if (correctTaopiaoRegex.test(combinedIdentifier)) return "taopiao";
    }
    return undefined;
}

function getInternationalRouteType(itineraryCountrySegment) {
    const fifthFreedomRegex = /ES-BR|BR-ES|CA-CU|CU-CA|US-PA|PA-US|HU-BY|BY-HU/ig;
    if (fifthFreedomRegex.test(itineraryCountrySegment)) return "5thFreedom";
    return "I+I/6thFreedom";
}

function getChinaInternationalRouteType(flightNumbers, originDirectCountry, isRoundTripBehavior, aircraftTypes, dataXayerOmCountry, routeInputStringForRegexFn) {
    if (!flightNumbers && !routeInputStringForRegexFn) return "PtoP/ConnectingFlights";
    const testableFlightString = routeInputStringForRegexFn || flightNumbers;

    const airChinaCodeshareRegex = /CA[7][0123456][\d][\d]|CA[6][102456789][\d][\d]|CA[5][2325641960][\d][\d]/ig;
    const simpleFlightFormatRegex = /^\w{2}\d+$/ig;
    const roundTripFlightFormatRegex = /^\w{2}\d+-\/-\w{2}\d+$/ig;
    const ietFlightRegex = /^([\w/-]+-)*(((?!CA\d).)+?\d+([A-Z])?-?)+([\w/-]+-?)*$/i;
    const railCodeRegex = /9B/ig;

    // Priority for D+I if origin is CN and matches specific flight patterns (for Test 6)
    if (originDirectCountry === "CN") {
        if ((isRoundTripBehavior && isValidRoundTripRouteFormat(testableFlightString)) ||
            (!isRoundTripBehavior && (isValidOneWayRouteFormat(testableFlightString) || isMultiCityRoute(testableFlightString)))) {
            // This specific flight pattern XY1234-CA789 matches isValidOneWayRouteFormat.
            // It implies the first leg is non-CA, so it's IET-like but also D+I. Prioritize D+I.
            return "D+I";
        }
    }

    if ((isRoundTripBehavior && roundTripFlightFormatRegex.test(testableFlightString)) || 
        (!isRoundTripBehavior && simpleFlightFormatRegex.test(testableFlightString))) {
        if (airChinaCodeshareRegex.test(testableFlightString)) return "PointToPoint(codeShare)";
        return "PointToPoint"; // This correctly handles Test 1 (US-CN RT direct CA flights)
    }
    
    // Check for IET / Railway, but ensure D+I for CN origin was checked first
    if (ietFlightRegex.test(testableFlightString)) {
        if (railCodeRegex.test(testableFlightString)) {
            if (dataXayerOmCountry === "DE") return "DBrailway";
            if (dataXayerOmCountry === "IT" && aircraftTypes && aircraftTypes.indexOf("ITRail") !== -1) return "ITrailway";
        }
        // If origin is CN and it's IET, but didn't match specific D+I patterns above, it's likely D+I with an IET domestic leg.
        if (originDirectCountry === "CN") {
             // Test 6: XY1234-CA789. originDirectCountry=CN. isValidOneWayRouteFormat is true. So D+I is returned above.
             // If it was, e.g., CA123-XY456 (I+D with IET domestic leg), then originDirectCountry would not be CN.
            return "D+I"; // If it's CN-originating and IET, and not a specific D+I pattern, it's D+I via IET.
        }
        return "IET"; 
    }

    if (airChinaCodeshareRegex.test(testableFlightString)) return "CodeShare(OverSeas)";

    // Fallback D+I or I+D if not caught by specific patterns above
    if (originDirectCountry === "CN") return "D+I";
    else return "I+D";
}

function determineRouteTypeRTOW(routeInputString) {
    if (!routeInputString || typeof routeInputString !== 'string') return undefined;
    const parts = routeInputString.split(':');
    if (parts.length < 4) return "Others"; 
    const routeCategory = parts[0]; 
    const directODcountries = parts[2]; 
    const wholeItineraryByCountry = parts[3]; 
    if (routeCategory === "MC") return undefined;
    const originDirectCountry = directODcountries.substr(0, 2); 
    const uniqueCountriesInItinerary = getUniqueArrayElementsExcludingSlash(wholeItineraryByCountry.split('-')).join('');
    
    // TAOPIAO check is not typically for RT/OW, but if it were, it'd be high priority.
    // For RT/OW, pureDOM is a primary check.
    if (uniqueCountriesInItinerary === "CN") return "pureDOM"; 

    const internationalToInternationalRegex = /^((?!CN).{2})-((?!CN).{2})$/ig; 
    const chinaToInternationalRegex = /^(CN-((?!CN).{2})|((?!CN).{2})-CN)$/ig; 
    const flightNumbers = dataXayer.wholefltNbr;
    const aircraftTypes = dataXayer.aircftTp;
    const omCountry = typeof omcountry !== 'undefined' ? omcountry : dataXayer.depCountry; 

    if (routeCategory === "OW") {
        if (internationalToInternationalRegex.test(wholeItineraryByCountry)) {
            return getInternationalRouteType(wholeItineraryByCountry);
        } else if (chinaToInternationalRegex.test(wholeItineraryByCountry)) {
            return getChinaInternationalRouteType(flightNumbers, originDirectCountry, false, aircraftTypes, omCountry, flightNumbers);
        }
    } else if (routeCategory === "RT") {
        if (internationalToInternationalRegex.test(directODcountries)) {
            return getInternationalRouteType(directODcountries);
        } else if (chinaToInternationalRegex.test(directODcountries)) {
             return getChinaInternationalRouteType(flightNumbers, originDirectCountry, true, aircraftTypes, omCountry, flightNumbers);
        }
    }
    return "Others"; 
}

function determineRouteTypeMC(routeInputString) {
    if (!routeInputString || typeof routeInputString !== 'string') return undefined;
    const parts = routeInputString.split(':');
    if (parts.length < 4) return "ConnectingFlights(MultiCity)"; 
    const routeCategory = parts[0]; 
    const directODcountries = parts[2]; 
    const wholeItineraryByCountry = parts[3]; 
    if (routeCategory !== "MC") return undefined; 

    const productsString = dataXayer.products; 
    const wholeItineraryCities = dataXayer.wholeIti; 
    const flightNumbers = dataXayer.wholefltNbr; 
    const aircraftTypes = dataXayer.aircftTp;
    const omCountry = typeof omcountry !== 'undefined' ? omcountry : dataXayer.depCountry;

    if (!productsString || !wholeItineraryCities || !flightNumbers) return "ConnectingFlights(MultiCity)";
    
    const overallOriginCity = extractProductData("b"); 
    const overallDestinationCity = extractProductData("c"); 
    const firstCityInItinerary = wholeItineraryCities.substring(0, 3);
    const lastCityInItinerary = wholeItineraryCities.slice(-3);
    const uniqueCountriesInItinerary = getUniqueArrayElementsExcludingSlash(wholeItineraryByCountry.split('-'));
    const uniqueCountriesString = uniqueCountriesInItinerary.join('');
    const originDirectCountry = directODcountries.substr(0, 2);

    // --- Priority Checks for specific MC types ---
    // Test 7 (TAOPIAO MC): Check Taopiao before pureDOM
    const isTaopiao = checkForTaopiao(wholeItineraryCities);
    if (isTaopiao === "taopiao") return "TAOPIAO";

    // pureDOM check (must be after Taopiao for CN-CN taopiao cases)
    if (uniqueCountriesString === "CN") return "pureDOM";

    // Test 8 (OpenJaw (OriginOJ) MC): Calculate OpenJaw type first.
    let openJawType = "";
    const cityItinerarySegments = wholeItineraryCities.split('/-'); 
    if (cityItinerarySegments.length > 1) {
        const firstLegDestinationCity = cityItinerarySegments[0].slice(-3);
        const secondLegOriginCity = cityItinerarySegments[1].substring(0, 3);
        if (firstLegDestinationCity !== secondLegOriginCity) {
            openJawType = "OpenJaw(TurnaroundOJ)";
        }
    }
    if (overallOriginCity !== firstCityInItinerary || overallDestinationCity !== lastCityInItinerary) {
        if (openJawType === "OpenJaw(TurnaroundOJ)") openJawType = "OpenJaw(DoubleOJ)";
        else openJawType = "OpenJaw(OriginOJ)";
    }
    
    // If OpenJaw is detected, it should generally take precedence over a generic IET,
    // unless the IET is a very specific type like railway.
    if (openJawType) {
        const railCodeRegex = /9B/ig;
        const isRailwayIET = railCodeRegex.test(flightNumbers) && 
                             (omCountry === "DE" || (omCountry === "IT" && aircraftTypes && aircraftTypes.indexOf("ITRail") !== -1));
        if (!isRailwayIET) { // If it's OpenJaw and not a special Railway IET, classify as OpenJaw.
            return openJawType;
        }
        // If it IS a railway IET and also OpenJaw, the railway classification might be more specific.
        // This means if isRailwayIET is true, we let it fall through to IET checks below.
    }
    // --- End OpenJaw Prioritization ---

    const airChinaCodeshareRegex = /CA[7][0123456][\d][\d]|CA[6][102456789][\d][\d]|CA[5][2325641960][\d][\d]/ig;
    const ietFlightRegex = /^([\w/-]+-)*(((?!CA\d).)+?\d+([A-Z])?-?)+([\w/-]+-?)*$/i;
    const railCodeRegex = /9B/ig; 

    // Test 2 (Multi-City US-CN-JP with IET flights, expected I+I/6thFreedom)
    if (ietFlightRegex.test(flightNumbers)) {
        // Check for specific IET types (railway) first
        if (railCodeRegex.test(flightNumbers)) {
            if (omCountry === "DE") return "DBrailway";
            if (omCountry === "IT" && aircraftTypes && aircraftTypes.indexOf("ITRail") !== -1) return "ITrailway";
        }
        // If it's IET, but also fits the criteria for I+I/6thFreedom (e.g. US-CN-JP with non-CA legs)
        // then I+I/6thFreedom should be prioritized.
        if (uniqueCountriesInItinerary.length >= 3) {
            const internationalViaChinaRegex = /^((?!CN).{2})-CN-((?!CN).{2})/ig; // e.g. US-CN-JP
            let simplifiedCountryItinerary = wholeItineraryByCountry.replace(/\/\-/g, "-"); // US-CN-JP-/-DE-FR -> US-CN-JP-DE-FR
             // Test if CN is a transit point between two OTHER international countries.
            if (internationalViaChinaRegex.test(simplifiedCountryItinerary) && directODcountries !== "CN-CN") {
                return "I+I/6thFreedom"; 
            }
        }
        // If it's IET and not a more specific I+I/6thFreedom or railway, then it's generic IET.
        // This handles cases where OpenJaw was detected but it was a railway IET (fell through).
        if (openJawType && (railCodeRegex.test(flightNumbers) && (omCountry === "DE" || (omCountry === "IT" && aircraftTypes && aircraftTypes.indexOf("ITRail") !== -1)))) {
             // If it was an OpenJaw Railway, return the railway type
            if (omCountry === "DE") return "DBrailway";
            if (omCountry === "IT" && aircraftTypes && aircraftTypes.indexOf("ITRail") !== -1) return "ITrailway";
        }
        return "IET"; 
    }
    
    if (airChinaCodeshareRegex.test(flightNumbers)) return "CodeShare(OverSeas)";
    
    // --- Country-based Logic (after specific types) ---
    if (uniqueCountriesInItinerary.length >= 3) {
        const internationalViaChinaRegex = /^((?!CN).{2})-CN-((?!CN).{2})/ig; 
        let simplifiedCountryItinerary = wholeItineraryByCountry.replace(/\/\-/g, "-"); 
        if (internationalViaChinaRegex.test(simplifiedCountryItinerary) && directODcountries !== "CN-CN") {
            return "I+I/6thFreedom";
        }
        if (countRegexMatches("CN", wholeItineraryByCountry) === 0 && directODcountries !== "CN-CN") {
            return "I+I/6thFreedom";
        }
    } else if (uniqueCountriesInItinerary.length === 2) {
        const fifthFreedomTestString = uniqueCountriesString.replace("CN", "");
        if (fifthFreedomTestString.length === 4) { 
            const testPair = fifthFreedomTestString.substr(0,2) + "-" + fifthFreedomTestString.substr(2,2);
            if (getInternationalRouteType(testPair) === "5thFreedom") return "5thFreedom";
        }
        if (countRegexMatches("CN", uniqueCountriesString) === 0) return "I+I/6thFreedom";
    }
    
    if (countRegexMatches("CN", wholeItineraryByCountry) >= 1) {
        if (isMultiCityRoute(flightNumbers)) { 
             if (originDirectCountry === "CN") return "D+I";
             else return "I+D";
        }
    }
    
    // If openJawType was determined but no other more specific category matched.
    if (openJawType) return openJawType; 

    return "ConnectingFlights(MultiCity)"; 
}

function runDebug() {
    console.log("--- Starting Debug Run ---");
    dataXayer = {}; 

    // --- Test Case 1: Round Trip (US-CN) ---
    dataXayer.routeType = "RT"; 
    dataXayer.cabin = "E"; 
    dataXayer.depandArrCountry = "US-CN"; 
    dataXayer.wholeitibyCountry = "US-CN-/-CN-US"; 
    dataXayer.aircftTp = "777:330"; 
    dataXayer.wholefltNbr = "CA986-/-CA985"; 
    dataXayer.products = ";RT:SFO-PEK:SFO-PEK-/-PEK-SFO:E:Ad"; 
    dataXayer.depCountry = "US"; 
    dataXayer.arrCountry = "CN";
    dataXayer.wholeIti = "SFO-PEK-/-PEK-SFO"; 

    console.log("--- Test Case: Round Trip (US-CN) ---");
    let seVar68_rt = dataXayer.routeType + ":" + dataXayer.cabin + ":" + dataXayer.depandArrCountry + ":" + dataXayer.wholeitibyCountry;
    let result_rt = determineRouteTypeRTOW(seVar68_rt);
    console.log("Input for RTOW: " + seVar68_rt);
    console.log("Calculated Route Type: " + result_rt); // Expected: PointToPoint (as CA986/CA985 are direct)
    let seVar62_rt = dataXayer.routeType + ":" + getRegionForCity(dataXayer.depCountry) + "-" + getRegionForCity(dataXayer.arrCountry);
    console.log("Route Type with Regions: " + seVar62_rt); 
    console.log("--- End Test Case ---");
    
    // --- Test Case 2: Multi-City (US-CN-JP) ---
    dataXayer.routeType = "MC";
    dataXayer.cabin = "Y";
    dataXayer.depandArrCountry = "US-JP"; 
    dataXayer.wholeitibyCountry = "US-CN-JP"; 
    dataXayer.wholefltNbr = "UA123-CA456-JL789"; 
    dataXayer.products = ";MC:LAX-NRT:LAX-PEK-NRT:Y:Ad"; 
    dataXayer.depCountry = "US";
    dataXayer.arrCountry = "JP";
    dataXayer.wholeIti = "LAX-PEK-NRT";
    
    console.log("--- Test Case: Multi-City (US-CN-JP) ---");
    let seVar68_mc = dataXayer.routeType + ":" + dataXayer.cabin + ":" + dataXayer.depandArrCountry + ":" + dataXayer.wholeitibyCountry;
    let result_mc = determineRouteTypeMC(seVar68_mc); 
    console.log("Input for MC: " + seVar68_mc);
    console.log("Calculated Route Type for MC: " + result_mc); // Expected: I+I/6thFreedom 
    let seVar62_mc = dataXayer.routeType + ":" + getRegionForCity(dataXayer.depCountry) + "-" + getRegionForCity(dataXayer.arrCountry);
    console.log("Route Type with Regions for MC: " + seVar62_mc); 
    console.log("--- End Test Case ---");

    // --- Test Case 3: Pure Domestic (CN-CN), One-Way ---
    dataXayer.routeType = "OW";
    dataXayer.cabin = "Y";
    dataXayer.depandArrCountry = "CN-CN";
    dataXayer.wholeitibyCountry = "CN-CN";
    dataXayer.wholefltNbr = "CA1832";
    dataXayer.products = ";OW:PEK-SHA:PEK-SHA:Y:Ad";
    dataXayer.depCountry = "CN";
    dataXayer.arrCountry = "CN";
    dataXayer.wholeIti = "PEK-SHA";

    console.log("--- Test Case: Pure Domestic OW (CN-CN) ---");
    let seVar68_dom_ow = dataXayer.routeType + ":" + dataXayer.cabin + ":" + dataXayer.depandArrCountry + ":" + dataXayer.wholeitibyCountry;
    let result_dom_ow = determineRouteTypeRTOW(seVar68_dom_ow);
    console.log("Input for RTOW (Domestic OW): " + seVar68_dom_ow);
    console.log("Calculated Route Type (Domestic OW): " + result_dom_ow); // Expected: pureDOM
    console.log("--- End Test Case ---");
    
    // --- Test Case 4: International to International (DE-FR), Round Trip ---
    dataXayer.routeType = "RT";
    dataXayer.cabin = "C";
    dataXayer.depandArrCountry = "DE-FR";
    dataXayer.wholeitibyCountry = "DE-FR-/-FR-DE";
    dataXayer.wholefltNbr = "LH100-/-LH101"; 
    dataXayer.products = ";RT:FRA-CDG:FRA-CDG-/-CDG-FRA:C:Ad";
    dataXayer.depCountry = "DE";
    dataXayer.arrCountry = "FR";
    dataXayer.wholeIti = "FRA-CDG-/-CDG-FRA";

    console.log("--- Test Case: Intl to Intl RT (DE-FR) ---");
    let seVar68_intl_rt = dataXayer.routeType + ":" + dataXayer.cabin + ":" + dataXayer.depandArrCountry + ":" + dataXayer.wholeitibyCountry;
    let result_intl_rt = determineRouteTypeRTOW(seVar68_intl_rt);
    console.log("Input for RTOW (Intl-Intl RT): " + seVar68_intl_rt);
    console.log("Calculated Route Type (Intl-Intl RT): " + result_intl_rt); // Expected: I+I/6thFreedom
    console.log("--- End Test Case ---");

    // --- Test Case 5: Fifth Freedom (ES-BR), One-Way ---
    dataXayer.routeType = "OW";
    dataXayer.cabin = "Y";
    dataXayer.depandArrCountry = "ES-BR"; 
    dataXayer.wholeitibyCountry = "ES-BR"; 
    dataXayer.wholefltNbr = "IB6827"; 
    dataXayer.products = ";OW:MAD-GRU:MAD-GRU:Y:Ad";
    dataXayer.depCountry = "ES"; 
    dataXayer.arrCountry = "BR"; 
    dataXayer.wholeIti = "MAD-GRU";

    console.log("--- Test Case: Fifth Freedom OW (ES-BR) ---");
    let seVar68_5th_ow = dataXayer.routeType + ":" + dataXayer.cabin + ":" + dataXayer.depandArrCountry + ":" + dataXayer.wholeitibyCountry;
    let result_5th_ow = determineRouteTypeRTOW(seVar68_5th_ow);
    console.log("Input for RTOW (5th Freedom OW): " + seVar68_5th_ow);
    console.log("Calculated Route Type (5th Freedom OW): " + result_5th_ow); // Expected: 5thFreedom
    console.log("--- End Test Case ---");

    // --- Test Case 6: D+I OW (CN-US) ---
    dataXayer.routeType = "OW";
    dataXayer.cabin = "Y";
    dataXayer.depandArrCountry = "CN-US";
    dataXayer.wholeitibyCountry = "CN-US"; 
    dataXayer.wholefltNbr = "XY1234-CA789"; // Intentionally an IET-like first leg then CA
    dataXayer.products = ";OW:PEK-JFK:PEK-JFK:Y:Ad"; 
    dataXayer.depCountry = "CN";
    dataXayer.arrCountry = "US";
    dataXayer.wholeIti = "PEK-JFK"; 

    console.log("--- Test Case: D+I OW (CN-US) ---");
    let seVar68_di_ow = dataXayer.routeType + ":" + dataXayer.cabin + ":" + dataXayer.depandArrCountry + ":" + dataXayer.wholeitibyCountry;
    let result_di_ow = determineRouteTypeRTOW(seVar68_di_ow);
    console.log("Input for RTOW (D+I OW): " + seVar68_di_ow);
    console.log("Calculated Route Type (D+I OW): " + result_di_ow); // Expected: D+I
    console.log("--- End Test Case ---");
    
    // --- Test Case 7: TAOPIAO MC ---
    dataXayer.routeType = "MC";
    dataXayer.cabin = "Y";
    dataXayer.depandArrCountry = "CN-CN"; 
    dataXayer.wholeitibyCountry = "CN-CN-/-CN-CN"; 
    dataXayer.wholefltNbr = "CA101/CA102"; 
    dataXayer.products = ";MC:PEK-PEK:PEK-SHA-/-SHA-PEK:Y:Ad";
    dataXayer.depCountry = "CN";
    dataXayer.arrCountry = "CN";
    dataXayer.wholeIti = "PEK-SHA-/-SHA-PEK"; 

    console.log("--- Test Case: TAOPIAO MC ---");
    let seVar68_taopiao_mc = dataXayer.routeType + ":" + dataXayer.cabin + ":" + dataXayer.depandArrCountry + ":" + dataXayer.wholeitibyCountry;
    let result_taopiao_mc = determineRouteTypeMC(seVar68_taopiao_mc);
    console.log("Input for MC (TAOPIAO): " + seVar68_taopiao_mc);
    console.log("Calculated Route Type (TAOPIAO): " + result_taopiao_mc); // Expected: TAOPIAO
    console.log("--- End Test Case ---");

    // --- Test Case 8: OpenJaw (OriginOJ) MC ---
    dataXayer.routeType = "MC";
    dataXayer.cabin = "C";
    dataXayer.depandArrCountry = "US-CA"; 
    dataXayer.wholeitibyCountry = "US-CA-/-CA-CA"; 
    dataXayer.wholefltNbr = "UA500/AC100-AC102"; // IET flights
    dataXayer.products = ";MC:SFO-YYZ:SFO-YVR-/-YUL-YYZ:C:Ad"; 
    dataXayer.depCountry = "US";
    dataXayer.arrCountry = "CA";
    dataXayer.wholeIti = "SFO-YVR-/-YUL-YYZ"; 

    console.log("--- Test Case: OpenJaw (OriginOJ) MC ---");
    let seVar68_oj_mc = dataXayer.routeType + ":" + dataXayer.cabin + ":" + dataXayer.depandArrCountry + ":" + dataXayer.wholeitibyCountry;
    let result_oj_mc = determineRouteTypeMC(seVar68_oj_mc);
    console.log("Input for MC (OriginOJ): " + seVar68_oj_mc);
    console.log("Calculated Route Type (OriginOJ): " + result_oj_mc); // Expected: OpenJaw(OriginOJ) or OpenJaw(DoubleOJ)
    console.log("--- End Test Case ---");
    
    console.log("--- Debug Run Finished ---");
}
// To run the debug examples:
// Node.js: save and run `node refactored_airline_route_logic.js`
// Browser: include in HTML, open console, call `runDebug()`.

runDebug();
