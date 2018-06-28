import Card from "@material-ui/core/Card";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import VisibilityIcon from "@material-ui/icons/Visibility";
import * as React from "react";

import { ListProps } from "../../..";
import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";

interface CollectionListProps extends ListProps {
  collections?: Array<{
    id: string;
    name: string;
    slug: string;
    isPublished: boolean;
    products: {
      totalCount: number;
    };
  }>;
}

const decorate = withStyles(theme => ({
  link: {
    color: theme.palette.secondary.main,
    cursor: "pointer" as "pointer"
  },
  textRight: {
    textAlign: "right" as "right"
  }
}));
const CollectionList = decorate<CollectionListProps>(
  ({
    classes,
    disabled,
    collections,
    pageInfo,
    onRowClick,
    onNextPage,
    onPreviousPage
  }) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{i18n.t("Name", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("Visibility", { context: "object" })}</TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Products", { context: "object" })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={3}
              hasNextPage={pageInfo && !disabled ? pageInfo.hasNextPage : false}
              onNextPage={onNextPage}
              hasPreviousPage={
                pageInfo && !disabled ? pageInfo.hasPreviousPage : false
              }
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {collections === undefined ? (
            <TableRow>
              <TableCell>
                <Skeleton />
              </TableCell>
              <TableCell>
                <Skeleton />
              </TableCell>
              <TableCell>
                <Skeleton />
              </TableCell>
            </TableRow>
          ) : collections.length > 0 ? (
            collections.map(collection => (
              <TableRow key={collection.id}>
                <TableCell
                  onClick={!!onRowClick ? onRowClick(collection.id) : undefined}
                  className={!!onRowClick ? classes.link : ""}
                >
                  {collection.name}
                </TableCell>
                <TableCell>
                  <StatusLabel
                    status={collection.isPublished ? "success" : "error"}
                    label={
                      collection.isPublished
                        ? i18n.t("Published")
                        : i18n.t("Not published")
                    }
                  />
                </TableCell>
                <TableCell className={classes.textRight}>
                  {collection.products.totalCount}
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={3}>
                {i18n.t("No collections found")}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
CollectionList.displayName = "CollectionList";
export default CollectionList;
