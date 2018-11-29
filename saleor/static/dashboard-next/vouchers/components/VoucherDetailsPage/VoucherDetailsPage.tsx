import DialogContentText from "@material-ui/core/DialogContentText";
import { withStyles } from "@material-ui/core/styles";
import * as CRC from "crc-32";
import * as React from "react";

import { createVoucherName, VoucherType } from "../..";
import ActionDialog from "../../../components/ActionDialog";
import { ConfirmButtonTransitionState } from "../../../components/ConfirmButton/ConfirmButton";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import SaveButtonBar from "../../../components/SaveButtonBar";
import Toggle from "../../../components/Toggle";
import i18n from "../../../i18n";
import VoucherDetails from "../VoucherDetails/VoucherDetails";
import VoucherProperties from "../VoucherProperties/VoucherProperties";
import VoucherUsability from "../VoucherUsability";

interface VoucherDetailsPageProps {
  disabled?: boolean;
  voucher?: {
    id: string;
    name: string | null;
    type: VoucherType;
    code: string;
    usageLimit: number | null;
    used: number | null;
    startDate: string;
    endDate: string | null;
    discountValueType: "PERCENTAGE" | "FIXED" | string;
    discountValue: number;
    product: {
      id: string;
      name: string;
      price: { amount: number; currency: string };
    } | null;
    category: {
      id: string;
      name: string;
      products: { totalCount: number };
    } | null;
    applyTo: string | null;
    limit: { amount: number; currency: string } | null;
  };
  currency?: string;
  categorySearchResults?: Array<{
    id: string;
    name: string;
  }>;
  productSearchResults?: Array<{
    id: string;
    name: string;
  }>;
  shippingSearchResults?: Array<{
    label: string;
    code: string;
  }>;
  saveButtonBarState?: ConfirmButtonTransitionState;
  loadingCategories?: boolean;
  loadingProducts?: boolean;
  loadingShipping?: boolean;
  fetchCategories?();
  fetchProducts?();
  fetchShipping?();
  onBack?();
  onVoucherDelete?();
}

const decorate = withStyles(theme => ({
  cardSpacer: {
    marginTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("md")]: {
      marginTop: theme.spacing.unit
    }
  },
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridTemplateColumns: "2fr 1fr"
  }
}));
const VoucherDetailsPage = decorate<VoucherDetailsPageProps>(
  ({
    classes,
    currency,
    disabled,
    categorySearchResults,
    saveButtonBarState,
    fetchCategories,
    fetchProducts,
    fetchShipping,
    loadingCategories,
    loadingProducts,
    loadingShipping,
    productSearchResults,
    shippingSearchResults,
    voucher,
    onBack,
    onVoucherDelete
  }) => (
    <Toggle>
      {(openedVoucherDeleteDialog, { toggle: toggleVoucherDeleteDialog }) => (
        <>
          <Form
            initial={{
              applyToAll:
                voucher && voucher.applyTo && voucher.type !== "SHIPPING"
                  ? voucher.applyTo === "all"
                  : null,
              applyToShipping:
                voucher && voucher.applyTo && voucher.type === "SHIPPING"
                  ? { label: voucher.applyTo, value: voucher.applyTo }
                  : null,
              category:
                voucher && voucher.category
                  ? { label: voucher.category.name, value: voucher.category.id }
                  : null,
              code: voucher && voucher.code ? voucher.code : "",
              discountValue:
                voucher && voucher.discountValue ? voucher.discountValue : 0,
              discountValueType:
                voucher && voucher.discountValueType
                  ? voucher.discountValueType
                  : "",
              endDate: voucher && voucher.endDate ? voucher.endDate : null,
              limit: voucher && voucher.limit ? voucher.limit.amount : null,
              name: voucher && voucher.name ? voucher.name : "",
              product:
                voucher && voucher.product
                  ? { label: voucher.product.name, value: voucher.product.id }
                  : null,
              startDate:
                voucher && voucher.startDate ? voucher.startDate : null,
              type: voucher && voucher.type ? voucher.type : "VALUE",
              usageLimit:
                voucher && voucher.usageLimit ? voucher.usageLimit : null
            }}
            key={voucher ? CRC.str(JSON.stringify(voucher)) : "loading"}
          >
            {({ change, data, hasChanged, submit }) => (
              <Container width="md">
                <PageHeader
                  title={
                    voucher
                      ? voucher.name !== null
                        ? voucher.name
                        : createVoucherName(voucher, currency)
                      : undefined
                  }
                  onBack={onBack}
                />
                <div className={classes.root}>
                  <div>
                    <VoucherDetails
                      currency={currency}
                      disabled={disabled}
                      voucher={voucher}
                      data={data}
                      onChange={change}
                    />
                    <div className={classes.cardSpacer} />
                    <VoucherProperties
                      disabled={disabled}
                      loadingCategories={loadingCategories}
                      loadingProducts={loadingProducts}
                      loadingShipping={loadingShipping}
                      categorySearchResults={categorySearchResults}
                      productSearchResults={productSearchResults}
                      shippingSearchResults={shippingSearchResults}
                      fetchCategories={fetchCategories}
                      fetchProducts={fetchProducts}
                      fetchShipping={fetchShipping}
                      voucher={voucher}
                      data={data}
                      onChange={change}
                    />
                  </div>
                  <div>
                    <VoucherUsability
                      disabled={disabled}
                      onChange={change}
                      data={data}
                    />
                  </div>
                </div>
                <SaveButtonBar
                  onCancel={onBack}
                  onDelete={toggleVoucherDeleteDialog}
                  onSave={submit}
                  state={saveButtonBarState}
                  disabled={disabled || !hasChanged}
                />
              </Container>
            )}
          </Form>
          {voucher !== undefined && (
            <ActionDialog
              confirmButtonState="default"
              open={openedVoucherDeleteDialog}
              onClose={toggleVoucherDeleteDialog}
              onConfirm={onVoucherDelete}
              title={i18n.t("Remove voucher")}
              variant="delete"
            >
              <DialogContentText
                dangerouslySetInnerHTML={{
                  __html: i18n.t(
                    "Are you sure you want to remove <strong>{{ name }}</strong>?",
                    { name: voucher.name }
                  )
                }}
              />
            </ActionDialog>
          )}
        </>
      )}
    </Toggle>
  )
);
VoucherDetailsPage.displayName = "VoucherDetailsPage";
export default VoucherDetailsPage;
