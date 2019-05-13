import Button from "@material-ui/core/Button";
import AddIcon from "@material-ui/icons/Add";
import * as React from "react";

import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { ListActions, PageListProps } from "../../../types";
import { VoucherList_vouchers_edges_node } from "../../types/VoucherList";
import VoucherList from "../VoucherList";

export interface VoucherListPageProps extends PageListProps, ListActions {
  defaultCurrency: string;
  vouchers: VoucherList_vouchers_edges_node[];
}

const VoucherListPage: React.StatelessComponent<VoucherListPageProps> = ({
  defaultCurrency,
  disabled,
  onAdd,
  onNextPage,
  onPreviousPage,
  onRowClick,
  pageInfo,
  vouchers,
  isChecked,
  selected,
  toggle,
  toolbar
}) => (
  <Container>
    <PageHeader title={i18n.t("Vouchers")}>
      <Button onClick={onAdd} variant="contained" color="primary">
        {i18n.t("Add voucher")}
        <AddIcon />
      </Button>
    </PageHeader>
    <VoucherList
      defaultCurrency={defaultCurrency}
      disabled={disabled}
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
      onRowClick={onRowClick}
      pageInfo={pageInfo}
      vouchers={vouchers}
      isChecked={isChecked}
      selected={selected}
      toggle={toggle}
      toolbar={toolbar}
    />
  </Container>
);
VoucherListPage.displayName = "VoucherListPage";
export default VoucherListPage;
