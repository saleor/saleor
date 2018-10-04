import Typography from "@material-ui/core/Typography";
import * as React from "react";

import { AddressType } from "../../customers/";
import Skeleton from "../Skeleton";

interface AddressFormatterProps {
  address?: AddressType;
}

const AddressFormatter: React.StatelessComponent<AddressFormatterProps> = ({
  address
}) => {
  if (!address) {
    return <Skeleton />;
  }
  return (
    <address>
      <Typography component="span">
        {address.firstName} {address.lastName}
      </Typography>
      {address.companyName && (
        <Typography component="span">{address.companyName}</Typography>
      )}
      <Typography component="span">
        {address.streetAddress1}
        <br />
        {address.streetAddress2}
      </Typography>
      <Typography component="span">
        {" "}
        {address.postalCode} {address.city}
        {address.cityArea ? ", " + address.cityArea : ""}
      </Typography>
      <Typography component="span">
        {address.countryArea
          ? address.countryArea + ", " + address.country.country
          : address.country.country}
      </Typography>
    </address>
  );
};
export default AddressFormatter;
