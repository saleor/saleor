import * as React from "react";

import useNavigator from "@hooks/useNavigator";
import useNotifier from "@hooks/useNotifier";
import useShop from "@hooks/useShop";
import i18n from "../../i18n";
import { getMutationState, maybe } from "../../misc";
import ShippingZoneCreatePage from "../components/ShippingZoneCreatePage";
import { TypedCreateShippingZone } from "../mutations";
import { CreateShippingZone } from "../types/CreateShippingZone";
import { shippingZonesListUrl, shippingZoneUrl } from "../urls";

const ShippingZoneCreate: React.StatelessComponent<{}> = () => {
  const navigate = useNavigator();
  const pushMessage = useNotifier();
  const shop = useShop();

  const onShippingZoneCreate = (data: CreateShippingZone) => {
    if (data.shippingZoneCreate.errors.length === 0) {
      pushMessage({
        text: i18n.t("Successfully created new shipping zone", {
          context: "notification"
        })
      });
      navigate(shippingZoneUrl(data.shippingZoneCreate.shippingZone.id));
    }
  };
  return (
    <TypedCreateShippingZone onCompleted={onShippingZoneCreate}>
      {(createShippingZone, createShippingZoneOpts) => {
        const formTransitionState = getMutationState(
          createShippingZoneOpts.called,
          createShippingZoneOpts.loading,
          maybe(() => createShippingZoneOpts.data.shippingZoneCreate.errors, [])
        );

        return (
          <ShippingZoneCreatePage
            countries={maybe(() => shop.countries, [])}
            disabled={createShippingZoneOpts.loading}
            errors={maybe(
              () => createShippingZoneOpts.data.shippingZoneCreate.errors
            )}
            onBack={() => navigate(shippingZonesListUrl())}
            onSubmit={formData =>
              createShippingZone({
                variables: {
                  input: formData
                }
              })
            }
            saveButtonBarState={formTransitionState}
          />
        );
      }}
    </TypedCreateShippingZone>
  );
};
export default ShippingZoneCreate;
