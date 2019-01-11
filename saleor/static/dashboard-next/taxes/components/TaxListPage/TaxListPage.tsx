import * as React from "react";

import { ListProps } from "../../../types";
import Container from "../../../components/Container";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";

export interface TaxListPageProps extends ListProps {
  taxes: any[];
}

const TaxListPage: React.StatelessComponent<TaxListPageProps> = ({
  disabled,
  pageInfo,
  taxes,
  onNextPage,
  onPreviousPage,
  onRowClick
}) => (
  <Container width="md">
    <PageHeader title={i18n.t("Staff members", { context: "page title" })} />
    <TaxList
      disabled={disabled}
      pageInfo={pageInfo}
      taxes={taxes}
      onNextPage={onNextPage}
      onPreviousPage={onPreviousPage}
      onRowClick={onRowClick}
    />
  </Container>
);
TaxListPage.displayName = "TaxListPage";
export default TaxListPage;
