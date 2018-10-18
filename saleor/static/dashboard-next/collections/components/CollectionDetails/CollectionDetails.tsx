import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import i18n from "../../../i18n";

export interface CollectionDetailsProps {
  data: {
    name: string;
  };
  disabled: boolean;
  errors: {
    name?: string;
  };
  onChange: (event: React.ChangeEvent<any>) => void;
}

const decorate = withStyles({
  name: {
    width: "80%"
  }
});
const CollectionDetails = decorate<CollectionDetailsProps>(
  ({ classes, disabled, data, onChange, errors }) => (
    <Card>
      <CardTitle title={i18n.t("General information")} />
      <CardContent>
        <TextField
          classes={{ root: classes.name }}
          label={i18n.t("Name")}
          name="name"
          disabled={disabled}
          value={data.name}
          onChange={onChange}
          error={!!errors.name}
          helperText={errors.name}
        />
      </CardContent>
    </Card>
  )
);
CollectionDetails.displayName = "CollectionDetails";
export default CollectionDetails;
