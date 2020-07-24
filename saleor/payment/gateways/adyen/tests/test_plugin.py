import json
from decimal import Decimal

import pytest

from .... import TransactionKind
from ....interface import GatewayResponse
from ....utils import create_payment_information, create_transaction


@pytest.mark.vcr
def test_get_payment_gateway_for_checkout(
    adyen_plugin, checkout_with_single_item, address
):
    checkout_with_single_item.billing_address = address
    checkout_with_single_item.save()
    adyen_plugin = adyen_plugin()
    response = adyen_plugin.get_payment_gateway_for_checkout(
        checkout_with_single_item, None
    )
    assert response.id == adyen_plugin.PLUGIN_ID
    assert response.name == adyen_plugin.PLUGIN_NAME
    config = response.config
    assert len(config) == 2
    assert config[0] == {
        "field": "origin_key",
        "value": adyen_plugin.config.connection_params["origin_key"],
    }
    assert config[1]["field"] == "config"
    config = json.loads(config[1]["value"])
    assert isinstance(config, list)


@pytest.mark.vcr
def test_process_payment(payment_adyen_for_checkout, checkout_with_items, adyen_plugin):
    payment_info = create_payment_information(
        payment_adyen_for_checkout,
        additional_data={"paymentMethod": {"paymentdata": ""}},
    )
    adyen_plugin = adyen_plugin()
    response = adyen_plugin.process_payment(payment_info, None)
    assert response.is_success is True
    assert response.action_required is False
    assert response.kind == TransactionKind.AUTH
    assert response.amount == Decimal("1234")
    assert response.currency == checkout_with_items.currency
    assert response.transaction_id == "882595494831959A"  # ID returned by Adyen
    assert response.error is None


@pytest.mark.vcr
def test_process_payment_with_auto_capture(
    payment_adyen_for_checkout, checkout_with_items, adyen_plugin
):
    payment_info = create_payment_information(
        payment_adyen_for_checkout,
        additional_data={"paymentMethod": {"paymentdata": ""}},
    )
    adyen_plugin = adyen_plugin(auto_capture=True)
    response = adyen_plugin.process_payment(payment_info, None)
    assert response.is_success is True
    assert response.action_required is False
    assert response.kind == TransactionKind.CAPTURE
    assert response.amount == Decimal("1234")
    assert response.currency == checkout_with_items.currency
    assert response.transaction_id == "882595494831959A"  # ID returned by Adyen
    assert response.error is None


@pytest.mark.vcr
def test_confirm_payment(payment_adyen_for_order, adyen_plugin):
    return  # teest it when we will have additional auth data
    payment_info = create_payment_information(
        payment_adyen_for_order,
        # additional_data={"paymentMethod": {'riskData': {'clientData': 'eyJ2ZXJzaW9uIjoiMS4wLjAiLCJkZXZpY2VGaW5nZXJwcmludCI6InJ5RUdYOGVacEowMDMwMDAwMDAwMDAwMDAwS1piSVFqNmt6czAwODkxNDY3NzZjVkI5NGlLekJHdmFtOUVxNm9WUTVTMTZHb2g1TWswMDRpdmJTdVlkRzBSMDAwMDBZVnhFcjAwMDAwY3J1OXNBeFRSNWlaQ3FuSTRsc2s6NDAiLCJwZXJzaXN0ZW50Q29va2llIjpbIl9ycF91aWQ9YzA0ZDE5OWEtYjkyYy1iZmQzLTI1YTMtNDJmM2ZjODdiN2UyIl0sImNvbXBvbmVudHMiOnsidXNlckFnZW50IjoiZmU5ZWMxM2NmMGFjODM4Y2YwYWVkMWM0NjJiYTUxODkiLCJsYW5ndWFnZSI6ImVuLUdCIiwiY29sb3JEZXB0aCI6MjQsImRldmljZU1lbW9yeSI6OCwicGl4ZWxSYXRpbyI6MSwiaGFyZHdhcmVDb25jdXJyZW5jeSI6OCwic2NyZWVuV2lkdGgiOjI1NjAsInNjcmVlbkhlaWdodCI6MTQ0MCwiYXZhaWxhYmxlU2NyZWVuV2lkdGgiOjI1NjAsImF2YWlsYWJsZVNjcmVlbkhlaWdodCI6MTQxNywidGltZXpvbmVPZmZzZXQiOi0xMjAsInRpbWV6b25lIjoiRXVyb3BlL1dhcnNhdyIsInNlc3Npb25TdG9yYWdlIjoxLCJsb2NhbFN0b3JhZ2UiOjEsImluZGV4ZWREYiI6MSwiYWRkQmVoYXZpb3IiOjAsIm9wZW5EYXRhYmFzZSI6MSwicGxhdGZvcm0iOiJNYWNJbnRlbCIsInBsdWdpbnMiOiJjMDhlOTc4YWIwMmUzNTk1YmZiOWNiN2ViZWZlZjMzMyIsImNhbnZhcyI6ImQ2MTY0ZTcwN2VkODQ3ZTUxODhhNWI1MjA4ZjQyNThiIiwid2ViZ2wiOiIwMzNkY2RlZjQ4YmY3NmY5MTMyY2M3MDlkZmY5YTA3MSIsIndlYmdsVmVuZG9yQW5kUmVuZGVyZXIiOiJJbnRlbCBJbmMufkludGVsKFIpIElyaXMoVE0pIFBsdXMgR3JhcGhpY3MgNjU1IiwiYWRCbG9jayI6MSwiaGFzTGllZExhbmd1YWdlcyI6MCwiaGFzTGllZFJlc29sdXRpb24iOjAsImhhc0xpZWRPcyI6MCwiaGFzTGllZEJyb3dzZXIiOjAsImZvbnRzIjoiMjkyZWEyY2NlY2NkMDJiMDFjMGM0YzFkNDEzMjE3NWUiLCJhdWRpbyI6IjQ3M2QxYzc0ZGI3Y2QzOGUxZmExNTgxN2IxMzY2YmZjIiwiZW51bWVyYXRlRGV2aWNlcyI6IjNiYzFkYTVmMzM1YTk5ZjE3NmJmMGUzYzgyNTFhMTkzIn19'}, 'paymentMethod': {'type': 'scheme', 'encryptedCardNumber': 'adyenjs_0_1_25$FakMVsJwQJd7jca8dYfL6xhLfXeWhqYhAOkqgqNF7yM+5Tl0boUG9Xk4dKFakS4/3lCIjomlgAmOt4vEGveFDJtljGyS7t1sElK+fUASA/AMsSMFcMBPPr8ybKqHNwwj6k4t9SagLUQX27m0hIMmOKwQLdwwJHE9Iw/D2rGRqbsamq8cmG+T2tHDeqt5YWRCoho8t1u+OMzJMsalfeYbJmI7uIfvjbHAa0LtM5X2B6DcOClqRfwmLg8AgR5Gr4NDPub7di/W9F9Qkt56nPkN9WEYTOA1HIWkgBGHkTwCBVCxKjHmQgcnH1SPf4kram5TUGT85p3J2/BL1QmpPZixtw==$u9MN2eUsQkAvlSPT3k7YvhE3YXNwp/CmrIArUrFMfTPoQiibd4boM9oGL3hIrE5rWyzvc+4P9q1coGAiW6FNgas1+ZifHzjs8bmPHYC2h0mrmdFu4MsJp6+RL+4B0C5sd0Ef1aUEW8wfFjOfE3NZVPibaUKT6iBFeAplfV73AQEmIh2TXvm9PEmWtvCPcmA2Z6C8u53VOn9b3Y0lq3E88WgNEX6dShRqcvsLpSkTzaXAYroXBSi0oCFu9ebtqMBtkGujPOZa+ULq7o651xDHlJPxGmGHzxJ2N6gxn7P/Fpdj9BJf9ZfEMmP4Artm86lN3OUudu7Dfo7qh46FZQ4UAbRmrEJVix/sHVP1Z30d6cGfsTi331NkNKomyjS53Mdp//jx43X7t+wZyxoIyDvk+buQhM5rCzpD8lyvffagJPQMvImajBjyXOEOFFy45yrXxwl1ZlCegzDyRzv7u3o6grqvobbSaZm8kHSvDGM8uAklwgUDfIcWqUWQeXPJpZPECY6wffjMixJG8nurmb/VBig9P33e/MJo79U6jgWyoRFT7Yp6OJ3egYp403d+EgZCSrpcjX0tc5PYuZth1kE0cjOYRD1XgmVC0rtn5dxqk7CxVC+S1pSLSdrtGVTj5tNDdunq1zCT1+zmasjjGLDzZ5p1JE4z9PccesH2nfuYwT2aEqalDCCGA2LPIFpM3dvFVYTVFsKo5n7LPAlakWSAC5+tZ9RL/SbtfPXb9erIN90WyDSwCZr9CD36xayWgoPP66y/Sc24nzoTE4LYx2FeAvs7aqIN4Mu0sUFMUMJEHHNsmvFzWBIveo+KmBiHYri9iXeNW6k+w6fk/zLE/yBuYsJFAKE5CFmd3LMdbZCCd/RS8g==', 'encryptedExpiryMonth': 'adyenjs_0_1_25$qG3iso+7U0Oa5iCydxxisgLaEJ2rBoamj5JhUXeHCvC5Gy7MgyHz6ztYib4Y7QFfferfmqH7gkFe7yDR94cKbhDt3d8ePSFAs+96SU93wYAYVWzn5dLPFiXhwtnhtk/7YCZaT5b4YKZJ/9bOWkU+CwHJ/y2ELhtx2MRDDSBOZOFjsm1K3LAvu8gNIKP8QhFxfT28qLmC1xlQHKjqlIpaEqJPs92Zi40dWhkrFIHE3lCfIlpJbVI4EW5xDD8l70wkmQsnCIhJ3toSdENk8vr0/AWlPPt4lzfLfIXN5MHuifsC3iReYiK9vzjkX4VQJTkfY+0SIo/S1Ccu84n0xLKVdA==$HZmDBPHVt+5u711J5pfTvS8ZT1fD443FnOkG+YwMxNZkF+ioUz3cdP/Cr3jHL1pFLxZfmtqJwpigG/5TOvJsF9QealVWD4tfWKQuxzEKeO3xNYS1D/rWWvjdjhz6Eb0satd+DKzZjmtPEiyPBQ9+01OFdm17FTEDq2V5JiqBIIKB7Erw9CpMSYxmdNzhsFQongwi6kZ2Ju1or+C/noecpi2YdX3X0JLLRuEEYE2SAHHKCQKfHpOl7sXVtJ1K5wOCZpH9pBmoEtETLxS/gOjONbhjbdwnZ6ovc7RH3V3pnqEuiFA8/RFVyQia/Jels6yRSSPXp0SQaGByNALFeVLDcfuX53sHm+IO9oHS69RBox/Es3Utxy80In7Q2Lel5eWL61E+RjQmlSS6Ua7yL8eGkucBxHhdY0a7K34V+kM7HyJd4WzWA93YOznkAU4Ezqpxz42hepGBFNbeUWaFc2Xb', 'encryptedExpiryYear': 'adyenjs_0_1_25$L+CzaH0ce+jzo4PXZPffqWIjDAshC38J+rywq/7CYRChqVZ14sPX0HSyymETGBqVCJebv22N0VWb3jKhpedTExqmXHiL/WnwmhpFcOKArUZIt60OBE1RZ6NSXJiQpaKgIofonVD32gtammLhljoyDeYTaTYuvHrbLLSyJSc0DUFxSVIUuMkwytXrpOL+jVYCRteYQ6Koxs1RIPy5v3+3JFMTNILpOi+jwaATbpHW6wGj1vhr+y7MQtlVqBvXNlbID5MXiYmUpqYPKEVSNFBoGCERU9d8N/FAsWmLThGVlzUub90M/N1UdjBljZrxTEpkY7wJah6DnMEqQ6PTLPJjJg==$Aqsbh5fcErzrb+7P+dHvofFP9PujIDsOACst8DEdaLiLNwPfPTAiCmYS6l+ev99v6i3BWBFdR1vvH0PfPKNxmLtSByGqf8c6xUoaIaVyBpYz6qpTHlj25e73ROhx9MGfFJtpgnHs8zM39+Y0AuCZ+lTtVgacMR28xkhyl88VjGUrq/jLESOpOS9VsgjjctlXsup5zr+/bL2JpUPkKYW0l3yx9aIZBjZXIkF6k0Ax8wdWMIjJyOOHYJfzUKR1zvDz8AkWxFdrTZWrKAfdMlI9+oyrPYfcxebnTyn7OxEc4blqCghlWxbzEgWdl29ez8rtzh2o6U3YL0gI2sQoSvwR9NUzZT37K5kXbEq/L5VPnDtfGV6pnnbN3335WVFDPAeSss7vSup6GusVDU3HMfKnKwf8a4/T3XmixVGI+CW/xlqIGEfY6/b77r/HA41LYo9i2T+UXhJyT8F7nd2+YCUxsA==', 'encryptedSecurityCode': 'adyenjs_0_1_25$VzWN+WT4DVd0BlT5Umwq4lgqvc00SxadFDbXfHm1VDlx/V1X5mpqYMizTcgKL+hfmyNjuic9NqHh9YBP7yZNJkoP61n2op1ZPO3gBklnAqKR9rGeCpkNvBgEUDIiuVTxNRzQD1UtKvWMX4RQeI0/vGKraNQCDbGQS1g+N4JUnzEnMmSUAq5GPKsoFijEP/UfXR2/Qh4g/AoyCwfmneDFG+YuqKa4LI563yRgODIKVZk+tYrzVGOw4Ass4R0kaHztcx7vk0haNur5MWsS0WzciuMhYfBu33qwW9i0P4yePxHEJdFlGCn+uxUFjmQj39Rch5xUUo6tkHP7b72Gn5xH3g==$uJDSyZJ8HNdG9q8REYbAVEHlnGuN/RRTQ6DGB3svlqheRY6tdqWnMS5g5nDJMT3VU+nEdvEpso21NhOiHGMhBTMd8UzMUYJqUbWwp/295Khvjpo5NNtwrmdQ74M2s5f19/Pn+6zwmC6HG+WFH7ZNTClLX8CqXa4iCEudho6IDg+Yf5RxCBO5Cvn30K2g6c16zMwNnNo/y7F8ejr8f2W+zvLtCPhLmb+8umvj8I65VHR+fr+aJ85w8WRSONOmFhdQTLbsUTnmuQHEksBTYfVK6kwTg661IfTgjaSdCmhs0gs0qBnSeVgTtizyO7rvKM6pfR5f78PVZPQWpOGhxGRqhu3TAc+4XZDSwh8B8Y0ofn98rucJpL3MgE+QHTn0AkBg9gtjmWWs0bNEFXBWDoAGfcs/ATCCfF74bgr2KstwOO3PBm7C4Y6ssPFsYqOomJGIZeCL+OAcEA+eeCDW/xjUEpPdiEZiIA3cAA=='}, 'browserInfo': {'acceptHeader': '*/*', 'colorDepth': 24, 'language': 'en-GB', 'javaEnabled': False, 'screenHeight': 1440, 'screenWidth': 2560, 'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36', 'timeZoneOffset': -120}}}
    )
    adyen_plugin = adyen_plugin()
    response = adyen_plugin.confirm_payment(payment_info, None)


@pytest.mark.vcr
def test_refund_payment(payment_adyen_for_order, order_with_lines, adyen_plugin):
    payment_info = create_payment_information(
        payment_adyen_for_order,
        # additional_data={"paymentMethod": {'riskData': {'clientData': 'eyJ2ZXJzaW9uIjoiMS4wLjAiLCJkZXZpY2VGaW5nZXJwcmludCI6InJ5RUdYOGVacEowMDMwMDAwMDAwMDAwMDAwS1piSVFqNmt6czAwODkxNDY3NzZjVkI5NGlLekJHdmFtOUVxNm9WUTVTMTZHb2g1TWswMDRpdmJTdVlkRzBSMDAwMDBZVnhFcjAwMDAwY3J1OXNBeFRSNWlaQ3FuSTRsc2s6NDAiLCJwZXJzaXN0ZW50Q29va2llIjpbIl9ycF91aWQ9YzA0ZDE5OWEtYjkyYy1iZmQzLTI1YTMtNDJmM2ZjODdiN2UyIl0sImNvbXBvbmVudHMiOnsidXNlckFnZW50IjoiZmU5ZWMxM2NmMGFjODM4Y2YwYWVkMWM0NjJiYTUxODkiLCJsYW5ndWFnZSI6ImVuLUdCIiwiY29sb3JEZXB0aCI6MjQsImRldmljZU1lbW9yeSI6OCwicGl4ZWxSYXRpbyI6MSwiaGFyZHdhcmVDb25jdXJyZW5jeSI6OCwic2NyZWVuV2lkdGgiOjI1NjAsInNjcmVlbkhlaWdodCI6MTQ0MCwiYXZhaWxhYmxlU2NyZWVuV2lkdGgiOjI1NjAsImF2YWlsYWJsZVNjcmVlbkhlaWdodCI6MTQxNywidGltZXpvbmVPZmZzZXQiOi0xMjAsInRpbWV6b25lIjoiRXVyb3BlL1dhcnNhdyIsInNlc3Npb25TdG9yYWdlIjoxLCJsb2NhbFN0b3JhZ2UiOjEsImluZGV4ZWREYiI6MSwiYWRkQmVoYXZpb3IiOjAsIm9wZW5EYXRhYmFzZSI6MSwicGxhdGZvcm0iOiJNYWNJbnRlbCIsInBsdWdpbnMiOiJjMDhlOTc4YWIwMmUzNTk1YmZiOWNiN2ViZWZlZjMzMyIsImNhbnZhcyI6ImQ2MTY0ZTcwN2VkODQ3ZTUxODhhNWI1MjA4ZjQyNThiIiwid2ViZ2wiOiIwMzNkY2RlZjQ4YmY3NmY5MTMyY2M3MDlkZmY5YTA3MSIsIndlYmdsVmVuZG9yQW5kUmVuZGVyZXIiOiJJbnRlbCBJbmMufkludGVsKFIpIElyaXMoVE0pIFBsdXMgR3JhcGhpY3MgNjU1IiwiYWRCbG9jayI6MSwiaGFzTGllZExhbmd1YWdlcyI6MCwiaGFzTGllZFJlc29sdXRpb24iOjAsImhhc0xpZWRPcyI6MCwiaGFzTGllZEJyb3dzZXIiOjAsImZvbnRzIjoiMjkyZWEyY2NlY2NkMDJiMDFjMGM0YzFkNDEzMjE3NWUiLCJhdWRpbyI6IjQ3M2QxYzc0ZGI3Y2QzOGUxZmExNTgxN2IxMzY2YmZjIiwiZW51bWVyYXRlRGV2aWNlcyI6IjNiYzFkYTVmMzM1YTk5ZjE3NmJmMGUzYzgyNTFhMTkzIn19'}, 'paymentMethod': {'type': 'scheme', 'encryptedCardNumber': 'adyenjs_0_1_25$FakMVsJwQJd7jca8dYfL6xhLfXeWhqYhAOkqgqNF7yM+5Tl0boUG9Xk4dKFakS4/3lCIjomlgAmOt4vEGveFDJtljGyS7t1sElK+fUASA/AMsSMFcMBPPr8ybKqHNwwj6k4t9SagLUQX27m0hIMmOKwQLdwwJHE9Iw/D2rGRqbsamq8cmG+T2tHDeqt5YWRCoho8t1u+OMzJMsalfeYbJmI7uIfvjbHAa0LtM5X2B6DcOClqRfwmLg8AgR5Gr4NDPub7di/W9F9Qkt56nPkN9WEYTOA1HIWkgBGHkTwCBVCxKjHmQgcnH1SPf4kram5TUGT85p3J2/BL1QmpPZixtw==$u9MN2eUsQkAvlSPT3k7YvhE3YXNwp/CmrIArUrFMfTPoQiibd4boM9oGL3hIrE5rWyzvc+4P9q1coGAiW6FNgas1+ZifHzjs8bmPHYC2h0mrmdFu4MsJp6+RL+4B0C5sd0Ef1aUEW8wfFjOfE3NZVPibaUKT6iBFeAplfV73AQEmIh2TXvm9PEmWtvCPcmA2Z6C8u53VOn9b3Y0lq3E88WgNEX6dShRqcvsLpSkTzaXAYroXBSi0oCFu9ebtqMBtkGujPOZa+ULq7o651xDHlJPxGmGHzxJ2N6gxn7P/Fpdj9BJf9ZfEMmP4Artm86lN3OUudu7Dfo7qh46FZQ4UAbRmrEJVix/sHVP1Z30d6cGfsTi331NkNKomyjS53Mdp//jx43X7t+wZyxoIyDvk+buQhM5rCzpD8lyvffagJPQMvImajBjyXOEOFFy45yrXxwl1ZlCegzDyRzv7u3o6grqvobbSaZm8kHSvDGM8uAklwgUDfIcWqUWQeXPJpZPECY6wffjMixJG8nurmb/VBig9P33e/MJo79U6jgWyoRFT7Yp6OJ3egYp403d+EgZCSrpcjX0tc5PYuZth1kE0cjOYRD1XgmVC0rtn5dxqk7CxVC+S1pSLSdrtGVTj5tNDdunq1zCT1+zmasjjGLDzZ5p1JE4z9PccesH2nfuYwT2aEqalDCCGA2LPIFpM3dvFVYTVFsKo5n7LPAlakWSAC5+tZ9RL/SbtfPXb9erIN90WyDSwCZr9CD36xayWgoPP66y/Sc24nzoTE4LYx2FeAvs7aqIN4Mu0sUFMUMJEHHNsmvFzWBIveo+KmBiHYri9iXeNW6k+w6fk/zLE/yBuYsJFAKE5CFmd3LMdbZCCd/RS8g==', 'encryptedExpiryMonth': 'adyenjs_0_1_25$qG3iso+7U0Oa5iCydxxisgLaEJ2rBoamj5JhUXeHCvC5Gy7MgyHz6ztYib4Y7QFfferfmqH7gkFe7yDR94cKbhDt3d8ePSFAs+96SU93wYAYVWzn5dLPFiXhwtnhtk/7YCZaT5b4YKZJ/9bOWkU+CwHJ/y2ELhtx2MRDDSBOZOFjsm1K3LAvu8gNIKP8QhFxfT28qLmC1xlQHKjqlIpaEqJPs92Zi40dWhkrFIHE3lCfIlpJbVI4EW5xDD8l70wkmQsnCIhJ3toSdENk8vr0/AWlPPt4lzfLfIXN5MHuifsC3iReYiK9vzjkX4VQJTkfY+0SIo/S1Ccu84n0xLKVdA==$HZmDBPHVt+5u711J5pfTvS8ZT1fD443FnOkG+YwMxNZkF+ioUz3cdP/Cr3jHL1pFLxZfmtqJwpigG/5TOvJsF9QealVWD4tfWKQuxzEKeO3xNYS1D/rWWvjdjhz6Eb0satd+DKzZjmtPEiyPBQ9+01OFdm17FTEDq2V5JiqBIIKB7Erw9CpMSYxmdNzhsFQongwi6kZ2Ju1or+C/noecpi2YdX3X0JLLRuEEYE2SAHHKCQKfHpOl7sXVtJ1K5wOCZpH9pBmoEtETLxS/gOjONbhjbdwnZ6ovc7RH3V3pnqEuiFA8/RFVyQia/Jels6yRSSPXp0SQaGByNALFeVLDcfuX53sHm+IO9oHS69RBox/Es3Utxy80In7Q2Lel5eWL61E+RjQmlSS6Ua7yL8eGkucBxHhdY0a7K34V+kM7HyJd4WzWA93YOznkAU4Ezqpxz42hepGBFNbeUWaFc2Xb', 'encryptedExpiryYear': 'adyenjs_0_1_25$L+CzaH0ce+jzo4PXZPffqWIjDAshC38J+rywq/7CYRChqVZ14sPX0HSyymETGBqVCJebv22N0VWb3jKhpedTExqmXHiL/WnwmhpFcOKArUZIt60OBE1RZ6NSXJiQpaKgIofonVD32gtammLhljoyDeYTaTYuvHrbLLSyJSc0DUFxSVIUuMkwytXrpOL+jVYCRteYQ6Koxs1RIPy5v3+3JFMTNILpOi+jwaATbpHW6wGj1vhr+y7MQtlVqBvXNlbID5MXiYmUpqYPKEVSNFBoGCERU9d8N/FAsWmLThGVlzUub90M/N1UdjBljZrxTEpkY7wJah6DnMEqQ6PTLPJjJg==$Aqsbh5fcErzrb+7P+dHvofFP9PujIDsOACst8DEdaLiLNwPfPTAiCmYS6l+ev99v6i3BWBFdR1vvH0PfPKNxmLtSByGqf8c6xUoaIaVyBpYz6qpTHlj25e73ROhx9MGfFJtpgnHs8zM39+Y0AuCZ+lTtVgacMR28xkhyl88VjGUrq/jLESOpOS9VsgjjctlXsup5zr+/bL2JpUPkKYW0l3yx9aIZBjZXIkF6k0Ax8wdWMIjJyOOHYJfzUKR1zvDz8AkWxFdrTZWrKAfdMlI9+oyrPYfcxebnTyn7OxEc4blqCghlWxbzEgWdl29ez8rtzh2o6U3YL0gI2sQoSvwR9NUzZT37K5kXbEq/L5VPnDtfGV6pnnbN3335WVFDPAeSss7vSup6GusVDU3HMfKnKwf8a4/T3XmixVGI+CW/xlqIGEfY6/b77r/HA41LYo9i2T+UXhJyT8F7nd2+YCUxsA==', 'encryptedSecurityCode': 'adyenjs_0_1_25$VzWN+WT4DVd0BlT5Umwq4lgqvc00SxadFDbXfHm1VDlx/V1X5mpqYMizTcgKL+hfmyNjuic9NqHh9YBP7yZNJkoP61n2op1ZPO3gBklnAqKR9rGeCpkNvBgEUDIiuVTxNRzQD1UtKvWMX4RQeI0/vGKraNQCDbGQS1g+N4JUnzEnMmSUAq5GPKsoFijEP/UfXR2/Qh4g/AoyCwfmneDFG+YuqKa4LI563yRgODIKVZk+tYrzVGOw4Ass4R0kaHztcx7vk0haNur5MWsS0WzciuMhYfBu33qwW9i0P4yePxHEJdFlGCn+uxUFjmQj39Rch5xUUo6tkHP7b72Gn5xH3g==$uJDSyZJ8HNdG9q8REYbAVEHlnGuN/RRTQ6DGB3svlqheRY6tdqWnMS5g5nDJMT3VU+nEdvEpso21NhOiHGMhBTMd8UzMUYJqUbWwp/295Khvjpo5NNtwrmdQ74M2s5f19/Pn+6zwmC6HG+WFH7ZNTClLX8CqXa4iCEudho6IDg+Yf5RxCBO5Cvn30K2g6c16zMwNnNo/y7F8ejr8f2W+zvLtCPhLmb+8umvj8I65VHR+fr+aJ85w8WRSONOmFhdQTLbsUTnmuQHEksBTYfVK6kwTg661IfTgjaSdCmhs0gs0qBnSeVgTtizyO7rvKM6pfR5f78PVZPQWpOGhxGRqhu3TAc+4XZDSwh8B8Y0ofn98rucJpL3MgE+QHTn0AkBg9gtjmWWs0bNEFXBWDoAGfcs/ATCCfF74bgr2KstwOO3PBm7C4Y6ssPFsYqOomJGIZeCL+OAcEA+eeCDW/xjUEpPdiEZiIA3cAA=='}, 'browserInfo': {'acceptHeader': '*/*', 'colorDepth': 24, 'language': 'en-GB', 'javaEnabled': False, 'screenHeight': 1440, 'screenWidth': 2560, 'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36', 'timeZoneOffset': -120}}}
    )
    gateway_response = GatewayResponse(
        kind=TransactionKind.AUTH,
        action_required=False,
        transaction_id="882595494831959A",
        is_success=False,
        amount=payment_info.amount,
        currency=payment_info.currency,
        error="",
        raw_response={},
    )

    create_transaction(
        payment=payment_adyen_for_order,
        payment_information=payment_info,
        kind=TransactionKind.AUTH,
        gateway_response=gateway_response,
    )
    response = adyen_plugin().refund_payment(payment_info, None)
    assert response.is_success is True
    assert response.action_required is False
    assert response.kind == TransactionKind.REFUND_ONGOING
    assert response.amount == Decimal("1234")
    assert response.currency == order_with_lines.currency
    assert response.transaction_id == "882595499620961A"  # ID returned by Adyen


@pytest.mark.vcr
def test_capture_payment(payment_adyen_for_order, order_with_lines, adyen_plugin):
    payment_info = create_payment_information(
        payment_adyen_for_order,
        # additional_data={"paymentMethod": {'riskData': {'clientData': 'eyJ2ZXJzaW9uIjoiMS4wLjAiLCJkZXZpY2VGaW5nZXJwcmludCI6InJ5RUdYOGVacEowMDMwMDAwMDAwMDAwMDAwS1piSVFqNmt6czAwODkxNDY3NzZjVkI5NGlLekJHdmFtOUVxNm9WUTVTMTZHb2g1TWswMDRpdmJTdVlkRzBSMDAwMDBZVnhFcjAwMDAwY3J1OXNBeFRSNWlaQ3FuSTRsc2s6NDAiLCJwZXJzaXN0ZW50Q29va2llIjpbIl9ycF91aWQ9YzA0ZDE5OWEtYjkyYy1iZmQzLTI1YTMtNDJmM2ZjODdiN2UyIl0sImNvbXBvbmVudHMiOnsidXNlckFnZW50IjoiZmU5ZWMxM2NmMGFjODM4Y2YwYWVkMWM0NjJiYTUxODkiLCJsYW5ndWFnZSI6ImVuLUdCIiwiY29sb3JEZXB0aCI6MjQsImRldmljZU1lbW9yeSI6OCwicGl4ZWxSYXRpbyI6MSwiaGFyZHdhcmVDb25jdXJyZW5jeSI6OCwic2NyZWVuV2lkdGgiOjI1NjAsInNjcmVlbkhlaWdodCI6MTQ0MCwiYXZhaWxhYmxlU2NyZWVuV2lkdGgiOjI1NjAsImF2YWlsYWJsZVNjcmVlbkhlaWdodCI6MTQxNywidGltZXpvbmVPZmZzZXQiOi0xMjAsInRpbWV6b25lIjoiRXVyb3BlL1dhcnNhdyIsInNlc3Npb25TdG9yYWdlIjoxLCJsb2NhbFN0b3JhZ2UiOjEsImluZGV4ZWREYiI6MSwiYWRkQmVoYXZpb3IiOjAsIm9wZW5EYXRhYmFzZSI6MSwicGxhdGZvcm0iOiJNYWNJbnRlbCIsInBsdWdpbnMiOiJjMDhlOTc4YWIwMmUzNTk1YmZiOWNiN2ViZWZlZjMzMyIsImNhbnZhcyI6ImQ2MTY0ZTcwN2VkODQ3ZTUxODhhNWI1MjA4ZjQyNThiIiwid2ViZ2wiOiIwMzNkY2RlZjQ4YmY3NmY5MTMyY2M3MDlkZmY5YTA3MSIsIndlYmdsVmVuZG9yQW5kUmVuZGVyZXIiOiJJbnRlbCBJbmMufkludGVsKFIpIElyaXMoVE0pIFBsdXMgR3JhcGhpY3MgNjU1IiwiYWRCbG9jayI6MSwiaGFzTGllZExhbmd1YWdlcyI6MCwiaGFzTGllZFJlc29sdXRpb24iOjAsImhhc0xpZWRPcyI6MCwiaGFzTGllZEJyb3dzZXIiOjAsImZvbnRzIjoiMjkyZWEyY2NlY2NkMDJiMDFjMGM0YzFkNDEzMjE3NWUiLCJhdWRpbyI6IjQ3M2QxYzc0ZGI3Y2QzOGUxZmExNTgxN2IxMzY2YmZjIiwiZW51bWVyYXRlRGV2aWNlcyI6IjNiYzFkYTVmMzM1YTk5ZjE3NmJmMGUzYzgyNTFhMTkzIn19'}, 'paymentMethod': {'type': 'scheme', 'encryptedCardNumber': 'adyenjs_0_1_25$FakMVsJwQJd7jca8dYfL6xhLfXeWhqYhAOkqgqNF7yM+5Tl0boUG9Xk4dKFakS4/3lCIjomlgAmOt4vEGveFDJtljGyS7t1sElK+fUASA/AMsSMFcMBPPr8ybKqHNwwj6k4t9SagLUQX27m0hIMmOKwQLdwwJHE9Iw/D2rGRqbsamq8cmG+T2tHDeqt5YWRCoho8t1u+OMzJMsalfeYbJmI7uIfvjbHAa0LtM5X2B6DcOClqRfwmLg8AgR5Gr4NDPub7di/W9F9Qkt56nPkN9WEYTOA1HIWkgBGHkTwCBVCxKjHmQgcnH1SPf4kram5TUGT85p3J2/BL1QmpPZixtw==$u9MN2eUsQkAvlSPT3k7YvhE3YXNwp/CmrIArUrFMfTPoQiibd4boM9oGL3hIrE5rWyzvc+4P9q1coGAiW6FNgas1+ZifHzjs8bmPHYC2h0mrmdFu4MsJp6+RL+4B0C5sd0Ef1aUEW8wfFjOfE3NZVPibaUKT6iBFeAplfV73AQEmIh2TXvm9PEmWtvCPcmA2Z6C8u53VOn9b3Y0lq3E88WgNEX6dShRqcvsLpSkTzaXAYroXBSi0oCFu9ebtqMBtkGujPOZa+ULq7o651xDHlJPxGmGHzxJ2N6gxn7P/Fpdj9BJf9ZfEMmP4Artm86lN3OUudu7Dfo7qh46FZQ4UAbRmrEJVix/sHVP1Z30d6cGfsTi331NkNKomyjS53Mdp//jx43X7t+wZyxoIyDvk+buQhM5rCzpD8lyvffagJPQMvImajBjyXOEOFFy45yrXxwl1ZlCegzDyRzv7u3o6grqvobbSaZm8kHSvDGM8uAklwgUDfIcWqUWQeXPJpZPECY6wffjMixJG8nurmb/VBig9P33e/MJo79U6jgWyoRFT7Yp6OJ3egYp403d+EgZCSrpcjX0tc5PYuZth1kE0cjOYRD1XgmVC0rtn5dxqk7CxVC+S1pSLSdrtGVTj5tNDdunq1zCT1+zmasjjGLDzZ5p1JE4z9PccesH2nfuYwT2aEqalDCCGA2LPIFpM3dvFVYTVFsKo5n7LPAlakWSAC5+tZ9RL/SbtfPXb9erIN90WyDSwCZr9CD36xayWgoPP66y/Sc24nzoTE4LYx2FeAvs7aqIN4Mu0sUFMUMJEHHNsmvFzWBIveo+KmBiHYri9iXeNW6k+w6fk/zLE/yBuYsJFAKE5CFmd3LMdbZCCd/RS8g==', 'encryptedExpiryMonth': 'adyenjs_0_1_25$qG3iso+7U0Oa5iCydxxisgLaEJ2rBoamj5JhUXeHCvC5Gy7MgyHz6ztYib4Y7QFfferfmqH7gkFe7yDR94cKbhDt3d8ePSFAs+96SU93wYAYVWzn5dLPFiXhwtnhtk/7YCZaT5b4YKZJ/9bOWkU+CwHJ/y2ELhtx2MRDDSBOZOFjsm1K3LAvu8gNIKP8QhFxfT28qLmC1xlQHKjqlIpaEqJPs92Zi40dWhkrFIHE3lCfIlpJbVI4EW5xDD8l70wkmQsnCIhJ3toSdENk8vr0/AWlPPt4lzfLfIXN5MHuifsC3iReYiK9vzjkX4VQJTkfY+0SIo/S1Ccu84n0xLKVdA==$HZmDBPHVt+5u711J5pfTvS8ZT1fD443FnOkG+YwMxNZkF+ioUz3cdP/Cr3jHL1pFLxZfmtqJwpigG/5TOvJsF9QealVWD4tfWKQuxzEKeO3xNYS1D/rWWvjdjhz6Eb0satd+DKzZjmtPEiyPBQ9+01OFdm17FTEDq2V5JiqBIIKB7Erw9CpMSYxmdNzhsFQongwi6kZ2Ju1or+C/noecpi2YdX3X0JLLRuEEYE2SAHHKCQKfHpOl7sXVtJ1K5wOCZpH9pBmoEtETLxS/gOjONbhjbdwnZ6ovc7RH3V3pnqEuiFA8/RFVyQia/Jels6yRSSPXp0SQaGByNALFeVLDcfuX53sHm+IO9oHS69RBox/Es3Utxy80In7Q2Lel5eWL61E+RjQmlSS6Ua7yL8eGkucBxHhdY0a7K34V+kM7HyJd4WzWA93YOznkAU4Ezqpxz42hepGBFNbeUWaFc2Xb', 'encryptedExpiryYear': 'adyenjs_0_1_25$L+CzaH0ce+jzo4PXZPffqWIjDAshC38J+rywq/7CYRChqVZ14sPX0HSyymETGBqVCJebv22N0VWb3jKhpedTExqmXHiL/WnwmhpFcOKArUZIt60OBE1RZ6NSXJiQpaKgIofonVD32gtammLhljoyDeYTaTYuvHrbLLSyJSc0DUFxSVIUuMkwytXrpOL+jVYCRteYQ6Koxs1RIPy5v3+3JFMTNILpOi+jwaATbpHW6wGj1vhr+y7MQtlVqBvXNlbID5MXiYmUpqYPKEVSNFBoGCERU9d8N/FAsWmLThGVlzUub90M/N1UdjBljZrxTEpkY7wJah6DnMEqQ6PTLPJjJg==$Aqsbh5fcErzrb+7P+dHvofFP9PujIDsOACst8DEdaLiLNwPfPTAiCmYS6l+ev99v6i3BWBFdR1vvH0PfPKNxmLtSByGqf8c6xUoaIaVyBpYz6qpTHlj25e73ROhx9MGfFJtpgnHs8zM39+Y0AuCZ+lTtVgacMR28xkhyl88VjGUrq/jLESOpOS9VsgjjctlXsup5zr+/bL2JpUPkKYW0l3yx9aIZBjZXIkF6k0Ax8wdWMIjJyOOHYJfzUKR1zvDz8AkWxFdrTZWrKAfdMlI9+oyrPYfcxebnTyn7OxEc4blqCghlWxbzEgWdl29ez8rtzh2o6U3YL0gI2sQoSvwR9NUzZT37K5kXbEq/L5VPnDtfGV6pnnbN3335WVFDPAeSss7vSup6GusVDU3HMfKnKwf8a4/T3XmixVGI+CW/xlqIGEfY6/b77r/HA41LYo9i2T+UXhJyT8F7nd2+YCUxsA==', 'encryptedSecurityCode': 'adyenjs_0_1_25$VzWN+WT4DVd0BlT5Umwq4lgqvc00SxadFDbXfHm1VDlx/V1X5mpqYMizTcgKL+hfmyNjuic9NqHh9YBP7yZNJkoP61n2op1ZPO3gBklnAqKR9rGeCpkNvBgEUDIiuVTxNRzQD1UtKvWMX4RQeI0/vGKraNQCDbGQS1g+N4JUnzEnMmSUAq5GPKsoFijEP/UfXR2/Qh4g/AoyCwfmneDFG+YuqKa4LI563yRgODIKVZk+tYrzVGOw4Ass4R0kaHztcx7vk0haNur5MWsS0WzciuMhYfBu33qwW9i0P4yePxHEJdFlGCn+uxUFjmQj39Rch5xUUo6tkHP7b72Gn5xH3g==$uJDSyZJ8HNdG9q8REYbAVEHlnGuN/RRTQ6DGB3svlqheRY6tdqWnMS5g5nDJMT3VU+nEdvEpso21NhOiHGMhBTMd8UzMUYJqUbWwp/295Khvjpo5NNtwrmdQ74M2s5f19/Pn+6zwmC6HG+WFH7ZNTClLX8CqXa4iCEudho6IDg+Yf5RxCBO5Cvn30K2g6c16zMwNnNo/y7F8ejr8f2W+zvLtCPhLmb+8umvj8I65VHR+fr+aJ85w8WRSONOmFhdQTLbsUTnmuQHEksBTYfVK6kwTg661IfTgjaSdCmhs0gs0qBnSeVgTtizyO7rvKM6pfR5f78PVZPQWpOGhxGRqhu3TAc+4XZDSwh8B8Y0ofn98rucJpL3MgE+QHTn0AkBg9gtjmWWs0bNEFXBWDoAGfcs/ATCCfF74bgr2KstwOO3PBm7C4Y6ssPFsYqOomJGIZeCL+OAcEA+eeCDW/xjUEpPdiEZiIA3cAA=='}, 'browserInfo': {'acceptHeader': '*/*', 'colorDepth': 24, 'language': 'en-GB', 'javaEnabled': False, 'screenHeight': 1440, 'screenWidth': 2560, 'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36', 'timeZoneOffset': -120}}}
    )
    gateway_response = GatewayResponse(
        kind=TransactionKind.AUTH,
        action_required=False,
        transaction_id="882595494831959A",
        is_success=False,
        amount=payment_info.amount,
        currency=payment_info.currency,
        error="",
        raw_response={},
    )

    create_transaction(
        payment=payment_adyen_for_order,
        payment_information=payment_info,
        kind=TransactionKind.AUTH,
        gateway_response=gateway_response,
    )
    response = adyen_plugin().capture_payment(payment_info, None)
    assert response.is_success is True
    assert response.action_required is False
    assert response.kind == TransactionKind.CAPTURE
    assert response.amount == Decimal("1234")
    assert response.currency == order_with_lines.currency
    assert response.transaction_id == "852595499936560C"  # ID returned by Adyen
