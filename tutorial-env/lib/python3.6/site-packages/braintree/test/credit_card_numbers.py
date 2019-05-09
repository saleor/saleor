class CreditCardNumbers(object):
    class CardTypeIndicators(object):
        Commercial = "4111111111131010"
        DurbinRegulated = "4111161010101010"
        Debit = "4117101010101010"
        Healthcare = "4111111510101010"
        Payroll  = "4111111114101010"
        Prepaid = "4111111111111210"
        IssuingBank = "4111111141010101"
        CountryOfIssuance = "4111111111121102"

        No  = "4111111111310101"
        Unknown = "4111111111112101"

    Maestro = "6304000000000000" # :nodoc:
    MasterCard = "5555555555554444"
    MasterCardInternational = "5105105105105100" # :nodoc:

    Visa = "4012888888881881"
    VisaInternational = "4009348888881881" # :nodoc:
    VisaPrepaid = "4500600000000061"

    Discover = "6011111111111117"
    Elo = "5066991111111118"

    class FailsSandboxVerification(object):
        AmEx       = "378734493671000"
        Discover   = "6011000990139424"
        MasterCard = "5105105105105100"
        Visa       = "4000111111111115"

    class AmexPayWithPoints(object):
        Success            = "371260714673002"
        IneligibleCard     = "378267515471109"
        InsufficientPoints = "371544868764018"

    class Disputes(object):
        Chargeback = "4023898493988028"
