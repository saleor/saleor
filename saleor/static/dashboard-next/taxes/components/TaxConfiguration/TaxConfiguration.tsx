import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import CardActions from "@material-ui/core/CardActions";
import CardContent from "@material-ui/core/CardContent";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import ControlledSwitch from "../../../components/ControlledSwitch";
import FormSpacer from "../../../components/FormSpacer";
import Hr from "../../../components/Hr";
import i18n from "../../../i18n";
import { FormData } from "../CountryListPage";

interface TaxConfigurationProps {
  data: FormData;
  disabled: boolean;
  onChange: (event: React.ChangeEvent<any>) => void;
  onTaxFetch: () => void;
}

const styles = createStyles({
  content: {
    paddingBottom: 0
  }
});

export const TaxConfiguration = withStyles(styles, {
  name: "TaxConfiguration"
})(
  ({
    classes,
    data,
    disabled,
    onChange,
    onTaxFetch
  }: TaxConfigurationProps & WithStyles<typeof styles>) => (
    <Card>
      <CardTitle title={i18n.t("Configuration")} />
      <CardContent className={classes.content}>
        <ControlledSwitch
          disabled={disabled}
          name={"includeTax" as keyof FormData}
          label={i18n.t("All products prices are entered with tax included")}
          onChange={onChange}
          checked={data.includeTax}
        />
        <ControlledSwitch
          disabled={disabled}
          name={"showGross" as keyof FormData}
          label={i18n.t("Show gross prices to customers in the storefront")}
          onChange={onChange}
          checked={data.showGross}
        />
        <ControlledSwitch
          disabled={disabled}
          name={"chargeTaxesOnShipping" as keyof FormData}
          label={i18n.t("Charge taxes on shipping rates")}
          onChange={onChange}
          checked={data.chargeTaxesOnShipping}
        />
        <FormSpacer />
      </CardContent>
      <Hr />
      <CardActions>
        <Button
          disabled={disabled}
          onClick={onTaxFetch}
          variant="flat"
          color="primary"
        >
          {i18n.t("Fetch taxes")}
        </Button>
      </CardActions>
    </Card>
  )
);
export default TaxConfiguration;
