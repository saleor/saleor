from typing import Dict, Iterable, List

UNKNOWN_ERROR = "Unknown error while processing the payment."


TRANSACTION_REGISTRATION_RESULT_ERRORS = {
    "E0100048": "Please make sure that the customer's name (Kanji) has been entered.",
    "E0100049": (
        "Please confirm that the customer’s name (Kanji) "
        "does not include prohibited characters."
    ),
    "E0100050": (
        "Please confirm that the customer’s name "
        "(Kanji) is within 21 full-width characters."
    ),
    "E0100051": (
        "Please confirm that the customer’s name "
        "(Kana) is within 25 full-width characters."
    ),
    "E0100052": (
        "Please confirm that the customer’s name "
        "(Kana) does not contain prohibited characters."
    ),
    "E0100053": (
        "Please confirm that your company's name is within 30 full-width characters."
    ),
    "E0100054": (
        "Please confirm that your company's name "
        "does not include prohibited characters."
    ),
    "E0100055": (
        "Please confirm that your department's name "
        "is within 30 full-width characters."
    ),
    "E0100056": (
        "Please confirm that your department's name "
        "does not include prohibited characters."
    ),
    "E0100057": "Please check if the customer’s ZIP code has been entered.",
    "E0100058": (
        "Please confirm that the customer’s ZIP code "
        "does not contain prohibited characters."
    ),
    "E0100136": (
        "Please check if the customer’s ZIP code "
        "format is correct. (Example: 1070052, 107 - 0052)"
    ),
    "E0100059": "Please check if the customer’s ZIP code and address match.",
    "E0100060": "Please make sure that the customer’s address has been entered.",
    "E0100061": (
        "Please make sure that the customer’s address "
        "does not contain prohibited characters."
    ),
    "E0100062": (
        "Please make sure that the customer’s address "
        "is within 55 full-width characters."
    ),
    "E0100063": "Please check if the customer’s phone number has been entered.",
    "E0100064": (
        "Please confirm that the customer’s phone number "
        "does not contain prohibited characters."
    ),
    "E0100065": "Please confirm that the format of the phone number is valid.",
    "E0100066": (
        "If the first to third digits of the phone number excluding the hyphen are "
        "“020”, “050”, “060”, “070”, “0 80”, or “0 90”, please ensure that "
        "the phone number has 11 digits."
    ),
    "E0100067": (
        "If the first to third digits of the phone number excluding the hyphen "
        "are other than the above, please check if it has 10 digits."
    ),
    "E0100068": "This item is required by merchants.",
    "E0100069": (
        "Please confirm that the customer’s email address "
        "does not contain prohibited characters."
    ),
    "E0100070": (
        "Please check if the customer’s email address is within 100 ASCII characters."
    ),
    "E0100071": "Please confirm that the format of the email address is valid.",
    "E0100072": "Please check if the delivery destination (Kanji) has been entered.",
    "E0100073": (
        "Please make sure that the delivery destination (Kanji) "
        "does not contain prohibited characters."
    ),
    "E0100074": (
        "Please confirm that the delivery destination (Kanji) "
        "is within 21 full-width characters."
    ),
    "E0100075": (
        "Please confirm that the delivery destination (Kana) "
        "is within 25 full-width characters."
    ),
    "E0100076": (
        "Please make sure that the delivery destination (Kana) "
        "does not contain prohibited characters."
    ),
    "E0100077": (
        "Please confirm that the delivery destination (company name) "
        "is within 30 full-width characters."
    ),
    "E0100078": (
        "Please confirm that the delivery destination (company name) "
        "does not include prohibited characters."
    ),
    "E0100079": (
        "Please confirm that the delivery destination (department name) "
        "is entered within 30 full-width characters."
    ),
    "E0100080": (
        "Please confirm that the delivery destination (department name) "
        "does not contain prohibited characters."
    ),
    "E0100081": "Please check if the delivery destination (ZIP code) has been entered.",
    "E0100082": (
        "Please make sure that the delivery destination (ZIP code) "
        "does not contain prohibited characters."
    ),
    "E0100137": (
        "Please check if the delivery destination (ZIP code) "
        "is in the correct format. (Example: 1070052, 107 - 0052)"
    ),
    "E0100083": (
        "Please make sure the delivery destination (ZIP code) and address match."
    ),
    "E0100084": "Please check if the delivery destination (address) has been entered.",
    "E0100085": (
        "Please make sure that the delivery destination (address) "
        "does not contain prohibited characters."
    ),
    "E0100086": (
        "Please confirm that the delivery destination (address) "
        "is within 55 full-width characters."
    ),
    "E0100087": (
        "Please check if the delivery destination (phone number) has been entered."
    ),
    "E0100088": (
        "Please make sure that the delivery destination (phone number) "
        "does not contain prohibited characters."
    ),
    "E0100089": "Please ensure the phone number format is valid.",
    "E0100090": (
        "If the 1 st to 3 rd digit of the phone number excluding the hyphen is "
        "“020”, “050”, “060”, “070”, “0 80”, or “0 90”, please ensure "
        "that the phone number has a total of 11 digits."
    ),
    "E0100091": "Please check if the delivery phone number is entered.",
}

TRANSACTION_CANCELLATION_RESULT_ERROR = {
    "EPRO0101": "Please confirm that at least one normal transaction is set.",
    "EPRO0102": (
        "Please confirm that 1, 000 or fewer sets of normal transactions are set."
    ),
    "EPRO0105": "Please check if the NP Transaction ID has been entered.",
    "EPRO0106": "Please check if the same NP Transaction ID is duplicated.",
    "E0100002": (
        "Please check if the NP Transaction ID is in "
        "half-width alphanumeric characters."
    ),
    "E0100003": "Please check if the NP Transaction ID is 11 digits.",
    "E0100113": "Please confirm that the transaction in question exists.",
    "EPRO0107": "Please confirm that the transaction s an NP card transaction.",
    "E0100114": "Please confirm that the transaction is prior to customer payment.",
    "E0100118": "Please confirm that the transaction is not cancelled.",
    "E0100131": (
        "Please confirm that the transaction is prior to returning to the merchant."
    ),
    "E0100132": "Please confirm that the payment method is as expected.",
}

FULFILLMENT_REPORT_RESULT_ERRORS = {
    "EPRO0101": "Please confirm that at least one normal transaction is set.",
    "EPRO0102": (
        "Please confirm that 1, 000 or fewer sets of normal transactions are set."
    ),
    "EPRO0105": "Please check if the NP Transaction ID has been entered.",
    "EPRO0106": "Please check if the same NP Transaction ID is duplicated.",
    "E0100002": (
        "Please check if the NP Transaction ID "
        "is in half-width alphanumeric characters."
    ),
    "E0100003": "Please check if the NP Transaction ID is 11 digits.",
    "E0100113": "",
    "EPRO0107": "",
    "E0100132": "",
    "E0100105": "",
    "E0100106": "",
    "E0100107": "",
    "E0100108": "",
    "E0100109": "",
    "E0100110": "",
    "EPRO0109": "If not entered, it will not be checked.",
    "E0100143": "The check is used only for NP Atobarai.",
    "E0100111": "The check is used only for NP Atobarai wiz.",
    "E0100124": "",
    "E0100126": "",
    "E0100114": "",
    "E0100115": "",
    "E0100118": "",
    "E0100120": "",
    "E0100121": "",
    "E0109002": (
        "This is an NP system error. Please contact the NP Support Desk if it occurs."
    ),
    "E0109003": (
        "This is an NP system error. Please contact the NP Support Desk if it occurs."
    ),
}


def get_error_messages_from_codes(
    error_codes: Iterable[str], error_map: Dict[str, str]
) -> List[str]:
    return [error_map.get(code, f"#{code}: {UNKNOWN_ERROR}") for code in error_codes]


UNKNOWN_REASON = "Unknown pending reason while processing the payment."


PendingReason = {
    "RE009": (
        "Please check your registered address, "
        "as there may be insufficient address information."
        "(1. Please enter the name of the building or room number. "
        "2. Please enter the name of the company or store in the “Company Name” box.)"
    ),
    "RE014": (
        "NP atobarai cannot be used for deliveries to temporary destinations "
        "(hotels, etc.) or for picking up items at post offices, convenience stores, "
        "or shipping company offices.Please check your registered address "
        "and the enrollment status of the purchaser in provided address. "
        "Please contact the NP Support Desk if you are eligible to use NP atobarai, "
        "for example, if you are a staff member."
    ),
    "RE015": (
        "Please check your registered shipping address, "
        "as the address information may be insufficient. "
        "(1. Please enter the name of the building or room number. "
        "2. Please enter the name of the company or store in the “Company Name” field.)"
    ),
    "RE020": (
        "NP atobarai is not available for deliveries to temporary destinations "
        "(hotels, etc.) or for picking up items at post offices, convenience stores, "
        "or shipping company offices. Please check your registered address "
        "and the enrollment status of the purchaser in provided address. "
        "Please contact the NP Support Desk if it is available to use NP atobarai "
        "such as order by a staff member."
    ),
    "RE021": (
        "Provided phone number has something wrong and it caused an error. "
        "Please update your phone number."
    ),
    "RE023": (
        "Provided phone number for the shipping address has something wrong "
        "and it caused an error. Please update your phone number."
    ),
    "RE026": (
        "If the registered address is to P.O. Box, if you are an employee of the "
        "merchant (in-house transactions), if the website is not examined yet, "
        "if you only charge shipping and handling fee, if you sell prohibited products "
        "(including digital content, animals, tickets, course fees, etc., which you "
        "have started selling after we have completed our review of the merchant), "
        "please cancel the transaction if it applies to any of the above."
    ),
}


def get_reason_messages_from_codes(
    reason_codes: Iterable[str],
) -> List[str]:
    return [
        # The number of pending codes may increase in the future.
        PendingReason.get(code, f"#{code}: {UNKNOWN_REASON}")
        for code in reason_codes
    ]
