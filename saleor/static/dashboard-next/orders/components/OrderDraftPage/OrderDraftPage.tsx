import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import { CardMenu } from "../../../components/CardMenu/CardMenu";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import { Container } from "../../../components/Container";
import DateFormatter from "../../../components/DateFormatter";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { DraftOrderInput } from "../../../types/globalTypes";
import { OrderDetails_order } from "../../types/OrderDetails";
import { UserSearch_customers_edges_node } from "../../types/UserSearch";
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
    },
    menu: {
      marginRight: -theme.spacing.unit
    },
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "9fr 4fr"
    }
  });

export interface OrderDraftPageProps extends WithStyles<typeof styles> {
  disabled: boolean;
  order: OrderDetails_order;
  users: UserSearch_customers_edges_node[];
  usersLoading: boolean;
  countries: Array<{
    code: string;
    label: string;
  }>;
  saveButtonBarState: ConfirmButtonTransitionState;
  variants: Array<{
    id: string;
    name: string;
    sku: string;
    stockQuantity: number;
  }>;
  variantsLoading: boolean;
  fetchVariants: (value: string) => void;
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
    order,
    users,
    usersLoading
  }: OrderDraftPageProps) => (
    <Container width="md">
      <PageHeader
        className={classes.header}
        title={maybe(() => order.number) ? "#" + order.number : undefined}
        onBack={onBack}
      >
        <CardMenu
          className={classes.menu}
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
            <DateFormatter date={order.created} />
          </Typography>
        ) : (
          <Skeleton style={{ width: "10em" }} />
        )}
      </div>
      <div className={classes.root}>
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
          />
        </div>
      </div>
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
