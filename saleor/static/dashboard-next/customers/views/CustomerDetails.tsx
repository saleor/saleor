import * as React from "react";

import Navigator from "../../components/Navigator";
import CustomerDetailsPage from "../components/CustomerDetailsPage/CustomerDetailsPage";
import { TypedCustomerDetailsQuery } from "../queries";
import { customerListUrl, customerUrl } from "../urls";

interface CustomerDetailsViewProps {
  id: string;
}

export const CustomerDetailsView: React.StatelessComponent<
  CustomerDetailsViewProps
> = ({ id }) => (
  <Navigator>
    {navigate => (
      <TypedCustomerDetailsQuery variables={{ id }}>
        {customerDetails => (
          <CustomerDetailsPage
            customer={customerDetails.data.user}
            disabled={customerDetails.loading}
            onAddressManageClick={() => undefined} // TODO: add address management
            onBack={() => navigate(customerListUrl)}
            onDelete={() => undefined} // TODO: add delete modal
            onRowClick={id => () =>
              navigate(customerUrl(encodeURIComponent(id)))}
            onSubmit={() => undefined} // TODO: add mutations
            onViewAllOrdersClick={() => undefined} // TODO: add filters to order
          />
        )}
      </TypedCustomerDetailsQuery>
    )}
  </Navigator>
);
export default CustomerDetailsView;
