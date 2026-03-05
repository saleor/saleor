class ShippingMethodType:
    PRICE_BASED = "price"
    WEIGHT_BASED = "weight"
    MANUAL = "manual"

    CHOICES = [
        (PRICE_BASED, "Price based shipping"),
        (WEIGHT_BASED, "Weight based shipping"),
        (MANUAL, "Manual shipping"),
    ]


class PostalCodeRuleInclusionType:
    INCLUDE = "include"
    EXCLUDE = "exclude"

    CHOICES = [
        (INCLUDE, "Shipping method should include postal code rule"),
        (EXCLUDE, "Shipping method should exclude postal code rule"),
    ]


class IncoTerm:
    EXW = "EXW"
    FCA = "FCA"
    CPT = "CPT"
    CIP = "CIP"
    DAP = "DAP"
    DPU = "DPU"
    DDP = "DDP"
    FAS = "FAS"
    FOB = "FOB"
    CFR = "CFR"
    CIF = "CIF"

    CHOICES = [
        (EXW, "Ex Works"),
        (FCA, "Free Carrier"),
        (CPT, "Carriage Paid To"),
        (CIP, "Carriage and Insurance Paid To"),
        (DAP, "Delivered At Place"),
        (DPU, "Delivered at Place Unloaded"),
        (DDP, "Delivered Duty Paid"),
        (FAS, "Free Alongside Ship"),
        (FOB, "Free On Board"),
        (CFR, "Cost and Freight"),
        (CIF, "Cost Insurance and Freight"),
    ]

    BUYER_PAYS_SHIPPING = [EXW]
    ZERO_COST_ALLOWED = [EXW, FCA, CPT, CIP, DAP, DPU, DDP, FAS, FOB, CFR, CIF]
    COLLECTION_INCO_TERMS = [EXW, FCA]


class ShipmentType:
    INBOUND = "inbound"
    OUTBOUND = "outbound"

    CHOICES = [
        (INBOUND, "Inbound from supplier"),
        (OUTBOUND, "Outbound to customer"),
    ]
