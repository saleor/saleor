import Card from "@material-ui/core/Card";
import blue from "@material-ui/core/colors/blue";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface ProductPriceAndAvailabilityProps {
  collections?: Array<{
    id: string;
    name: string;
  }>;
  onRowClick(id: string);
}

const decorate = withStyles(theme => ({
  card: {
    marginTop: theme.spacing.unit * 2,
    [theme.breakpoints.down("sm")]: {
      marginTop: theme.spacing.unit
    }
  },
  link: {
    color: blue[500],
    cursor: "pointer"
  }
}));
export const ProductPriceAndAvailability = decorate<
  ProductPriceAndAvailabilityProps
>(({ classes, collections, onRowClick }) => (
  <Card className={classes.card}>
    <PageHeader title={i18n.t("Collections")} />
    <Table>
      <TableBody>
        {collections === undefined || collections === null ? (
          <TableRow>
            <TableCell>
              <Skeleton />
            </TableCell>
          </TableRow>
        ) : collections.length > 0 ? (
          collections.map(collection => (
            <TableRow key={collection.id}>
              <TableCell
                className={classes.link}
                onClick={onRowClick(collection.id)}
              >
                {collection.name}
              </TableCell>
            </TableRow>
          ))
        ) : (
          <TableRow>
            <TableCell>
              {i18n.t("This product is not in any collection")}
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  </Card>
));
export default ProductPriceAndAvailability;
