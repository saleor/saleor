import DialogContentText from "@material-ui/core/DialogContentText";
import { withStyles, WithStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import ActionDialog from "../../../components/ActionDialog";
import { CardMenu } from "../../../components/CardMenu/CardMenu";
import { Container } from "../../../components/Container";
import DateFormatter from "../../../components/DateFormatter";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import Skeleton from "../../../components/Skeleton";
import { AddressTypeInput } from "../../../customers/types";
import i18n from "../../../i18n";
import { maybe, transformAddressToForm } from "../../../misc";
import { UserError } from "../../../types";
import { DraftOrderInput } from "../../../types/globalTypes";
import { OrderDetails_order } from "../../types/OrderDetails";
import { UserSearch_customers_edges_node } from "../../types/UserSearch";
import OrderAddressEditDialog from "../OrderAddressEditDialog";
import OrderCustomer from "../OrderCustomer";
import OrderDraftDetails from "../OrderDraftDetails/OrderDraftDetails";
import { FormData as OrderDraftDetailsProductsFormData } from "../OrderDraftDetailsProducts";
import OrderHistory, { FormData as HistoryFormData } from "../OrderHistory";
import OrderProductAddDialog, {
  FormData as ProductAddFormData
} from "../OrderProductAddDialog";
import OrderShippingMethodEditDialog, {
  FormData as ShippingMethodForm
} from "../OrderShippingMethodEditDialog";

export interface OrderDraftPageProps {
  disabled: boolean;
  order: OrderDetails_order;
  users: UserSearch_customers_edges_node[];
  usersLoading: boolean;
  countries: Array<{
    code: string;
    label: string;
  }>;
  variants: Array<{
    id: string;
    name: string;
    sku: string;
    stockQuantity: number;
  }>;
  variantsLoading: boolean;
  errors: UserError[];
  fetchVariants: (value: string) => void;
  fetchUsers: (query: string) => void;
  onBack: () => void;
  onBillingAddressEdit: (data: AddressTypeInput) => void;
  onCustomerEdit: (data: DraftOrderInput) => void;
  onDraftFinalize: () => void;
  onDraftRemove: () => void;
  onNoteAdd: (data: HistoryFormData) => void;
  onOrderLineAdd: (data: ProductAddFormData) => void;
  onOrderLineChange: (
    id: string,
    data: OrderDraftDetailsProductsFormData
  ) => void;
  onOrderLineRemove: (id: string) => void;
  onProductClick: (id: string) => void;
  onShippingAddressEdit: (data: AddressTypeInput) => void;
  onShippingMethodEdit: (data: ShippingMethodForm) => void;
}
interface OrderDraftPageState {
  openedBillingAddressEditDialog: boolean;
  openedDraftRemoveDialog: boolean;
  openedDraftFinalizeDialog: boolean;
  openedOrderLineAddDialog: boolean;
  openedShippingAddressEditDialog: boolean;
  openedShippingMethodEditDialog: boolean;
}

const decorate = withStyles(theme => ({
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
}));
class OrderDraftPageComponent extends React.Component<
  OrderDraftPageProps & WithStyles<"date" | "header" | "menu" | "root">,
  OrderDraftPageState
> {
  state = {
    openedBillingAddressEditDialog: false,
    openedDraftFinalizeDialog: false,
    openedDraftRemoveDialog: false,
    openedOrderLineAddDialog: false,
    openedShippingAddressEditDialog: false,
    openedShippingMethodEditDialog: false
  };

  toggleDraftRemoveDialog = () =>
    this.setState(prevState => ({
      openedDraftRemoveDialog: !prevState.openedDraftRemoveDialog
    }));
  toggleDraftFinalizeDialog = () =>
    this.setState(prevState => ({
      openedDraftFinalizeDialog: !prevState.openedDraftFinalizeDialog
    }));
  toggleOrderLineAddDialog = () =>
    this.setState(prevState => ({
      openedOrderLineAddDialog: !prevState.openedOrderLineAddDialog
    }));
  toggleShippingAddressEditDialog = () =>
    this.setState(prevState => ({
      openedShippingAddressEditDialog: !prevState.openedShippingAddressEditDialog
    }));
  toggleBillingAddressEditDialog = () =>
    this.setState(prevState => ({
      openedBillingAddressEditDialog: !prevState.openedBillingAddressEditDialog
    }));
  toggleShippingMethodEditDialog = () =>
    this.setState(prevState => ({
      openedShippingMethodEditDialog: !prevState.openedShippingMethodEditDialog
    }));

  render() {
    const {
      classes,
      countries,
      disabled,
      errors,
      order,
      users,
      usersLoading,
      variants,
      variantsLoading,
      fetchUsers,
      fetchVariants,
      onBack,
      onBillingAddressEdit,
      onCustomerEdit,
      onDraftRemove,
      onDraftFinalize,
      onNoteAdd,
      onOrderLineAdd,
      onOrderLineChange,
      onOrderLineRemove,
      onShippingAddressEdit,
      onShippingMethodEdit
    } = this.props;
    const {
      openedBillingAddressEditDialog,
      openedDraftFinalizeDialog,
      openedDraftRemoveDialog,
      openedOrderLineAddDialog,
      openedShippingAddressEditDialog,
      openedShippingMethodEditDialog
    } = this.state;
    return (
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
                onSelect: this.toggleDraftRemoveDialog
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
              onOrderLineAdd={this.toggleOrderLineAddDialog}
              onOrderLineChange={onOrderLineChange}
              onOrderLineRemove={onOrderLineRemove}
              onShippingMethodEdit={this.toggleShippingMethodEditDialog}
            />
            <OrderProductAddDialog
              loading={variantsLoading}
              open={openedOrderLineAddDialog}
              variants={variants}
              fetchVariants={fetchVariants}
              onClose={this.toggleOrderLineAddDialog}
              onSubmit={onOrderLineAdd}
            />
            <OrderShippingMethodEditDialog
              open={openedShippingMethodEditDialog}
              shippingMethod={maybe(() => order.shippingMethod.id, "")}
              shippingMethods={maybe(() => order.availableShippingMethods)}
              onClose={this.toggleShippingMethodEditDialog}
              onSubmit={onShippingMethodEdit}
            />
            <ActionDialog
              onClose={this.toggleDraftRemoveDialog}
              onConfirm={onDraftRemove}
              open={openedDraftRemoveDialog}
              title={i18n.t("Remove draft order", {
                context: "modal title"
              })}
              variant="delete"
            >
              <DialogContentText
                dangerouslySetInnerHTML={{
                  __html: i18n.t(
                    "Are you sure you want to remove draft <strong>#{{ number }}</strong>",
                    {
                      context: "modal",
                      number: maybe(() => order.number)
                    }
                  )
                }}
              />
            </ActionDialog>
            <ActionDialog
              onClose={this.toggleDraftFinalizeDialog}
              onConfirm={onDraftFinalize}
              open={openedDraftFinalizeDialog}
              title={i18n.t("Finalize draft order", {
                context: "modal title"
              })}
            >
              <DialogContentText
                dangerouslySetInnerHTML={{
                  __html: i18n.t(
                    "Are you sure you want to finalize draft <strong>#{{ number }}</strong>",
                    {
                      context: "modal",
                      number: maybe(() => order.number)
                    }
                  )
                }}
              />
            </ActionDialog>
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
              onBillingAddressEdit={this.toggleBillingAddressEditDialog}
              onCustomerEdit={onCustomerEdit}
              onShippingAddressEdit={this.toggleShippingAddressEditDialog}
            />
            {order && (
              <>
                <Form
                  initial={transformAddressToForm(
                    maybe(() => order.shippingAddress)
                  )}
                  errors={errors}
                  onSubmit={onShippingAddressEdit}
                >
                  {({ change, data, errors: formErrors, submit }) => (
                    <OrderAddressEditDialog
                      countries={countries}
                      data={data}
                      errors={formErrors}
                      open={openedShippingAddressEditDialog}
                      variant="shipping"
                      onChange={change}
                      onClose={this.toggleShippingAddressEditDialog}
                      onConfirm={submit}
                    />
                  )}
                </Form>
                <Form
                  initial={transformAddressToForm(order.billingAddress)}
                  errors={errors}
                  onSubmit={onBillingAddressEdit}
                >
                  {({ change, data, errors: formErrors, submit }) => (
                    <OrderAddressEditDialog
                      countries={countries}
                      data={data}
                      errors={formErrors}
                      open={openedBillingAddressEditDialog}
                      variant="billing"
                      onChange={change}
                      onClose={this.toggleBillingAddressEditDialog}
                      onConfirm={submit}
                    />
                  )}
                </Form>
              </>
            )}
          </div>
        </div>
        <SaveButtonBar
          disabled={disabled || maybe(() => order.lines.length === 0)}
          onCancel={onBack}
          onSave={this.toggleDraftFinalizeDialog}
          labels={{ save: i18n.t("Finalize", { context: "button" }) }}
        />
      </Container>
    );
  }
}
const OrderDetailsPage = decorate<OrderDraftPageProps>(OrderDraftPageComponent);
export default OrderDetailsPage;
