import * as React from "react";

import Messages from "../../components/messages";
import Navigator from "../../components/Navigator";
import { WindowTitle } from "../../components/WindowTitle";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import i18n from "../../i18n";
import { maybe } from "../../misc";
import CustomerAddressListPage from "../components/CustomerAddressListPage";
import { TypedSetCustomerDefaultAddressMutation } from "../mutations";
import { TypedCustomerAddressesQuery } from "../queries";
import { customerUrl } from "../urls";

interface CustomerAddressesProps {
  id: string;
}

const CustomerAddresses: React.FC<CustomerAddressesProps> = ({ id }) => {
  const navigate = useNavigator();
  const notify = useNotifier();

  return (
    <TypedSetCustomerDefaultAddressMutation>
      {(setCustomerDefaultAddress, setCustomerDefaultAddressOpts) => (
        <TypedCustomerAddressesQuery variables={{ id }}>
          {customerData => {
            return (
              <>
                <WindowTitle
                  title={maybe(() => customerData.data.user.firstName)}
                />
                <CustomerAddressListPage
                  customer={maybe(() => customerData.data.user)}
                  disabled={customerData.loading}
                  onAdd={() => undefined}
                  onBack={() =>
                    navigate(customerUrl(customerData.data.user.id))
                  }
                  onEdit={() => undefined}
                  onRemove={() => undefined}
                  onSetAsDefault={(id, type) =>
                    setCustomerDefaultAddress({
                      variables: { id, type }
                    })
                  }
                />
              </>
            );
          }}
        </TypedCustomerAddressesQuery>
      )}
    </TypedSetCustomerDefaultAddressMutation>
  );
};
export default CustomerAddresses;
