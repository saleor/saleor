import * as React from "react";

import CardSpacer from "../../../components/CardSpacer";
import Container from "../../../components/Container";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { ListProps } from "../../../types";
import { SaleType } from "../../../types/globalTypes";
import { SaleDetails_sale } from "../../types/SaleDetails";
import SaleInfo from "../SaleInfo";
import SalePricing from "../SalePricing";
import SaleSummary from "../SaleSummary";

export interface FormData {
  name: string;
  startDate: string;
  endDate: string;
  value: string;
  type: SaleType;
}

export interface SaleDetailsPageProps extends ListProps {
  activeTab: "categories" | "collections" | "products";
  defaultCurrency: string;
  sale: SaleDetails_sale;
  onBack: () => void;
  onRemove: () => void;
  onSubmit: (data: FormData) => void;
}

const SaleDetailsPage: React.StatelessComponent<SaleDetailsPageProps> = ({
  activeTab,
  defaultCurrency,
  disabled,
  sale,
  pageInfo,
  onBack,
  onNextPage,
  onPreviousPage,
  onRemove,
  onRowClick,
  onSubmit
}) => {
  const initialForm: FormData = {
    endDate: maybe(() => sale.endDate),
    name: maybe(() => sale.name),
    startDate: maybe(() => sale.startDate),
    type: maybe(() => sale.type),
    value: maybe(() => sale.value.toString())
  };
  return (
    <Form initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, errors, hasChanged, submit }) => (
        <Container width="md">
          <PageHeader title={maybe(() => sale.name)} onBack={onBack} />
          <Grid>
            <div>
              <SaleInfo data={data} disabled={disabled} onChange={change} />
              <CardSpacer />
              <SalePricing
                data={data}
                defaultCurrency={defaultCurrency}
                disabled={disabled}
                onChange={change}
              />
            </div>
            <div>
              <SaleSummary defaultCurrency={defaultCurrency} sale={sale} />
            </div>
          </Grid>
        </Container>
      )}
    </Form>
  );
};
SaleDetailsPage.displayName = "SaleDetailsPage";
export default SaleDetailsPage;
