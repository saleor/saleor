import * as React from "react";

import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import Shop from "../../components/Shop";
import { WindowTitle } from "../../components/WindowTitle";
import i18n from "../../i18n";
import { decimal, getMutationState, maybe } from "../../misc";
import {
  DiscountValueTypeEnum,
  VoucherDiscountValueType,
  VoucherTypeEnum
} from "../../types/globalTypes";
import VoucherCreatePage from "../components/VoucherCreatePage";
import { TypedVoucherCreate } from "../mutations";
import { VoucherCreate } from "../types/VoucherCreate";
import { voucherListUrl, voucherUrl } from "../urls";

function discountValueTypeEnum(
  type: VoucherDiscountValueType
): DiscountValueTypeEnum {
  return type.toString() === DiscountValueTypeEnum.FIXED
    ? DiscountValueTypeEnum.FIXED
    : DiscountValueTypeEnum.PERCENTAGE;
}

export const VoucherDetails: React.StatelessComponent = () => (
  <>
    <WindowTitle title={i18n.t("Vouchers")} />
    <Shop>
      {shop => (
        <Messages>
          {pushMessage => (
            <Navigator>
              {navigate => {
                const handleVoucherCreate = (data: VoucherCreate) => {
                  if (data.voucherCreate.errors.length === 0) {
                    pushMessage({
                      text: i18n.t("Successfully created voucher", {
                        context: "notification"
                      })
                    });
                    navigate(voucherUrl(data.voucherCreate.voucher.id), true);
                  }
                };

                return (
                  <TypedVoucherCreate onCompleted={handleVoucherCreate}>
                    {(voucherCreate, voucherCreateOpts) => {
                      const formTransitionState = getMutationState(
                        voucherCreateOpts.called,
                        voucherCreateOpts.loading,
                        maybe(() => voucherCreateOpts.data.voucherCreate.errors)
                      );

                      return (
                        <VoucherCreatePage
                          defaultCurrency={maybe(() => shop.defaultCurrency)}
                          disabled={voucherCreateOpts.loading}
                          errors={maybe(
                            () => voucherCreateOpts.data.voucherCreate.errors
                          )}
                          onBack={() => navigate(voucherListUrl())}
                          onSubmit={formData =>
                            voucherCreate({
                              variables: {
                                input: {
                                  code: formData.code,
                                  discountValue: decimal(formData.value),
                                  discountValueType: discountValueTypeEnum(
                                    formData.discountType
                                  ),
                                  endDate:
                                    formData.endDate === ""
                                      ? null
                                      : formData.endDate,
                                  minAmountSpent: formData.minAmountSpent,
                                  name: formData.name,
                                  startDate:
                                    formData.startDate === ""
                                      ? null
                                      : formData.startDate,
                                  type: VoucherTypeEnum[formData.type]
                                }
                              }
                            })
                          }
                          saveButtonBarState={formTransitionState}
                        />
                      );
                    }}
                  </TypedVoucherCreate>
                );
              }}
            </Navigator>
          )}
        </Messages>
      )}
    </Shop>
  </>
);
export default VoucherDetails;
