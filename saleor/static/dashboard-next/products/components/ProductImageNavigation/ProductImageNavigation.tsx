import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

import { ListProps } from "../../../";
import CardTitle from "../../../components/CardTitle";
import Skeleton from "../../../components/Skeleton";
import { TablePaginationActions } from "../../../components/TablePagination";
import i18n from "../../../i18n";

interface ProductImageNavigationProps extends ListProps {
  images?: Array<{
    id: string;
    url: string;
  }>;
  highlighted?: string;
}

const decorate = withStyles(theme => ({
  card: {
    marginBottom: 2 * theme.spacing.unit
  },
  image: {
    height: "100%",
    objectFit: "contain" as "contain",
    userSelect: "none" as "none",
    width: "100%"
  },
  imageContainer: {
    "&.highlighted": {
      borderColor: theme.palette.primary.main
    },
    background: "#ffffff",
    border: "2px solid #eaeaea",
    borderRadius: theme.spacing.unit,
    cursor: "pointer" as "pointer",
    height: 48,
    overflow: "hidden" as "hidden",
    padding: theme.spacing.unit / 2,
    position: "relative" as "relative"
  },
  root: {
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 2 + "px",
    gridRowGap: theme.spacing.unit + "px",
    gridTemplateColumns: "repeat(4, 1fr)"
  },
  toolbar: { marginTop: -theme.spacing.unit / 2 }
}));
const ProductImageNavigation = decorate<ProductImageNavigationProps>(
  ({
    classes,
    disabled,
    highlighted,
    images,
    onNextPage,
    onPreviousPage,
    onRowClick,
    pageInfo
  }) => (
    <Card className={classes.card}>
      <CardTitle
        title={i18n.t("All photos")}
        toolbar={
          <TablePaginationActions
            hasNextPage={!disabled && pageInfo.hasNextPage}
            hasPreviousPage={!disabled && pageInfo.hasPreviousPage}
            onNextPage={onNextPage}
            onPreviousPage={onPreviousPage}
            className={classes.toolbar}
          />
        }
      />
      <CardContent>
        {images === undefined ? (
          <Skeleton />
        ) : (
          <div className={classes.root}>
            {images.map(image => (
              <div
                className={[
                  classes.imageContainer,
                  image.id === highlighted ? "highlighted" : undefined
                ].join(" ")}
                onClick={onRowClick(image.id)}
                key={image.id}
              >
                <img className={classes.image} src={image.url} />
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
);
ProductImageNavigation.displayName = "ProductImageNavigation";
export default ProductImageNavigation;
