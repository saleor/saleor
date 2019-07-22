import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import React from "react";

import AppHeader from "@saleor/components/AppHeader";
import CardMenu from "@saleor/components/CardMenu";
import { ConfirmButtonTransitionState } from "@saleor/components/ConfirmButton";
import { Container } from "@saleor/components/Container";
import { DateTime } from "@saleor/components/Date";
import Grid from "@saleor/components/Grid";
import PageHeader from "@saleor/components/PageHeader";
import SaveButtonBar from "@saleor/components/SaveButtonBar";
import Skeleton from "@saleor/components/Skeleton";
import { SearchCustomers_customers_edges_node } from "../../../containers/SearchCustomers/types/SearchCustomers";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { DraftOrderInput } from "../../../types/globalTypes";
import { OrderDetails_order } from "../../types/OrderDetails";
import OrderCustomer from "../OrderCustomer";
import OrderDraftDetails from "../OrderDraftDetails/OrderDraftDetails";
import { FormData as OrderDraftDetailsProductsFormData } from "../OrderDraftDetailsProducts";
import OrderHistory, { FormData as HistoryFormData } from "../OrderHistory";

const styles = (theme: Theme) =>
  createStyles({
    date: {
      marginBottom: theme.spacing.unit * 3,
      marginLeft: theme.spacing.unit * 7
    },
    header: {
      marginBottom: 0
    }
  });

export interface OrderDraftPageProps extends WithStyles<typeof styles> {
  disabled: boolean;
  order: OrderDetails_order;
  users: SearchCustomers_customers_edges_node[];
  usersLoading: boolean;
  countries: Array<{
    code: string;
    label: string;
  }>;
  saveButtonBarState: ConfirmButtonTransitionState;
  fetchUsers: (query: string) => void;
  onBack: () => void;
  onBillingAddressEdit: () => void;
  onCustomerEdit: (data: DraftOrderInput) => void;
  onDraftFinalize: () => void;
  onDraftRemove: () => void;
  onNoteAdd: (data: HistoryFormData) => void;
  onOrderLineAdd: () => void;
  onOrderLineChange: (
    id: string,
    data: OrderDraftDetailsProductsFormData
  ) => void;
  onOrderLineRemove: (id: string) => void;
  onProductClick: (id: string) => void;
  onShippingAddressEdit: () => void;
  onShippingMethodEdit: () => void;
  onProfileView: () => void;
}

const OrderDraftPage = withStyles(styles, { name: "OrderDraftPage" })(
  ({
    classes,
    disabled,
    fetchUsers,
    saveButtonBarState,
    onBack,
    onBillingAddressEdit,
    onCustomerEdit,
    onDraftFinalize,
    onDraftRemove,
    onNoteAdd,
    onOrderLineAdd,
    onOrderLineChange,
    onOrderLineRemove,
    onShippingAddressEdit,
    onShippingMethodEdit,
    onProfileView,
    order,
    users,
    usersLoading
  }: OrderDraftPageProps) => (
    <Container>
      <AppHeader onBack={onBack}>{i18n.t("Orders")}</AppHeader>
      <PageHeader
        className={classes.header}
        title={maybe(() => order.number) ? "#" + order.number : undefined}
      >
        <CardMenu
          menuItems={[
            {
              label: i18n.t("Cancel order", { context: "button" }),
              onSelect: onDraftRemove
            }
          ]}
        />
      </PageHeader>
      <div className={classes.date}>
        {order && order.created ? (
          <Typography variant="caption">
            <DateTime date={order.created} />
          </Typography>
        ) : (
          <Skeleton style={{ width: "10em" }} />
        )}
      </div>
      <Grid>
        <div>
          <OrderDraftDetails
            order={order}
            onOrderLineAdd={onOrderLineAdd}
            onOrderLineChange={onOrderLineChange}
            onOrderLineRemove={onOrderLineRemove}
            onShippingMethodEdit={onShippingMethodEdit}
          />
          <OrderHistory
            history={maybe(() => order.events)}
            onNoteAdd={onNoteAdd}
          />
        </div>
        <div>
          <OrderCustomer
            canEditAddresses={true}
            canEditCustomer={true}
            order={order}
            users={users}
            loading={usersLoading}
            fetchUsers={fetchUsers}
            onBillingAddressEdit={onBillingAddressEdit}
            onCustomerEdit={onCustomerEdit}
            onShippingAddressEdit={onShippingAddressEdit}
            onProfileView={onProfileView}
          />
        </div>
      </Grid>
      <SaveButtonBar
        state={saveButtonBarState}
        disabled={disabled || !maybe(() => order.canFinalize)}
        onCancel={onBack}
        onSave={onDraftFinalize}
        labels={{ save: i18n.t("Finalize", { context: "button" }) }}
      />
    </Container>
  )
);
OrderDraftPage.displayName = "OrderDraftPage";
export default OrderDraftPage;
