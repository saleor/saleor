import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import { VoucherType } from "../..";
import { Container } from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { PageListProps } from "../../../types";
import VoucherList from "../VoucherList/VoucherList";

interface VoucherListPageProps extends PageListProps {
  currency?: string;
  vouchers?: Array<{
    id: string;
    name: string;
    type: VoucherType;
    code: string;
    usageLimit: number | null;
    used: number | null;
    startDate: string | null;
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
  }>;
}

const VoucherListPage: React.StatelessComponent<VoucherListPageProps> = ({
  currency,
  disabled,
  pageInfo,
  vouchers,
  onAdd,
  onNextPage,
  onPreviousPage,
  onRowClick
}) => (
  <Container width="md">
    <PageHeader title={i18n.t("Vouchers")}>
      <Button
        color="secondary"
        variant="contained"
        onClick={onAdd}
        disabled={disabled}
      >
        {i18n.t("Add voucher")} <AddIcon />
      </Button>
    </PageHeader>
    <VoucherList
      currency={currency}
      disabled={disabled}
      vouchers={vouchers}
      pageInfo={pageInfo}
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
      onRowClick={onRowClick}
    />
  </Container>
);
VoucherListPage.displayName = "VoucherListPage";
export default VoucherListPage;
