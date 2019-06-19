import { Theme } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableRow from "@material-ui/core/TableRow";
import makeStyles from "@material-ui/styles/makeStyles";
import * as React from "react";

import Checkbox from "@saleor/components/Checkbox";
import Skeleton from "@saleor/components/Skeleton";
import TableHead from "@saleor/components/TableHead";
import TablePagination from "@saleor/components/TablePagination";
import i18n from "@saleor/i18n";
import { renderCollection } from "@saleor/misc";
import { ListActions, ListProps } from "@saleor/types";
import { AttributeList_attributes_edges_node } from "../../types/AttributeList";

export interface AttributeListProps extends ListProps, ListActions {
  attributes: AttributeList_attributes_edges_node[];
}

const useStyles = makeStyles((theme: Theme) => ({
  [theme.breakpoints.up("lg")]: {
    colName: {
      width: "auto"
    },
    colSlug: {
      width: 200
    }
  },
  colName: {},
  colSlug: {},
  link: {
    cursor: "pointer"
  }
}));

const AttributeList: React.StatelessComponent<AttributeListProps> = ({
  attributes,
  disabled,
  isChecked,
  onNextPage,
  onPreviousPage,
  onRowClick,
  pageInfo,
  selected,
  toggle,
  toggleAll,
  toolbar
}) => {
  const classes = useStyles();

  return (
    <Table>
      <TableHead
        selected={selected}
        disabled={disabled}
        items={attributes}
        toggleAll={toggleAll}
        toolbar={toolbar}
      >
        <TableCell className={classes.colSlug}>
          {i18n.t("Attribute Code", { context: "attribute slug" })}
        </TableCell>
        <TableCell className={classes.colName}>
          {i18n.t("Default Label", { context: "attribute name" })}
        </TableCell>
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
        {renderCollection(
          attributes,
          attribute => {
            const isSelected = attribute ? isChecked(attribute.id) : false;

            return (
              <TableRow
                selected={isSelected}
                hover={!!attribute}
                key={attribute ? attribute.id : "skeleton"}
                onClick={attribute && onRowClick(attribute.id)}
                className={classes.link}
              >
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={isSelected}
                    disabled={disabled}
                    onChange={() => toggle(attribute.id)}
                  />
                </TableCell>
                <TableCell className={classes.colSlug}>
                  {attribute ? attribute.slug : <Skeleton />}
                </TableCell>
                <TableCell className={classes.colName}>
                  {attribute ? attribute.name : <Skeleton />}
                </TableCell>
              </TableRow>
            );
          },
          () => (
            <TableRow>
              <TableCell colSpan={3}>{i18n.t("No attributes found")}</TableCell>
            </TableRow>
          )
        )}
      </TableBody>
    </Table>
  );
};
AttributeList.displayName = "AttributeList";
export default AttributeList;
