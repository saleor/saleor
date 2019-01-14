import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import * as React from "react";

import { Container } from "../../../components/Container";
import Form from "../../../components/Form";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { maybe } from "../../../misc";
import { CountryList_shop } from "../../types/CountryList";
import CountryList from "../CountryList";
import TaxConfiguration from "../TaxConfiguration";

const styles = (theme: Theme) =>
  createStyles({
    root: {
      display: "grid",
      gridColumnGap: theme.spacing.unit * 2 + "px",
      gridTemplateColumns: "9fr 4fr"
    }
  });

export interface FormData {
  includeTax: boolean;
  showGross: boolean;
  chargeTaxesOnShipping: boolean;
}
export interface CountryListPageProps {
  disabled: boolean;
  shop: CountryList_shop;
  onRowClick: (code: string) => void;
  onSubmit: (data: FormData) => void;
  onTaxFetch: () => void;
}

const CountryListPage = withStyles(styles, { name: "CountryListPage" })(
  ({
    classes,
    disabled,
    shop,
    onRowClick,
    onSubmit,
    onTaxFetch
  }: CountryListPageProps & WithStyles<typeof styles>) => {
    const initialForm: FormData = {
      // TODO: connect to API
      // chargeTaxesOnShipping: maybe(() => shop.chargeTaxesOnShipping),
      chargeTaxesOnShipping: false,
      includeTax: maybe(() => shop.includeTaxesInPrices, false),
      showGross: maybe(() => shop.displayGrossPrices, false)
    };
    return (
      <Form initial={initialForm} onSubmit={onSubmit}>
        {({ change, data, submit }) => (
          <Container width="md">
            <PageHeader title={i18n.t("Taxes", { context: "page title" })} />
            <div className={classes.root}>
              <div>
                <CountryList
                  countries={maybe(() => shop.countries)}
                  onRowClick={onRowClick}
                />
              </div>
              <div>
                <TaxConfiguration
                  data={data}
                  disabled={disabled}
                  onChange={event => change(event, submit)}
                  onTaxFetch={onTaxFetch}
                />
              </div>
            </div>
          </Container>
        )}
      </Form>
    );
  }
);
CountryListPage.displayName = "CountryListPage";
export default CountryListPage;
