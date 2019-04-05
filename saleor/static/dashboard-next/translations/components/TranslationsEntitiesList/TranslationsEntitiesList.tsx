import { Omit } from "@material-ui/core";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as classNames from "classnames";
import * as React from "react";
import { ListProps } from "../../../types";

import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";

export interface TranslatableEntity {
  id: string;
  name: string;
  completion: {
    current: number;
    max: number;
  };
}

export interface TranslationsEntitiesListProps
  extends Omit<ListProps, "onRowClick"> {
  entities: TranslatableEntity[];
  onRowClick: (code: string) => void;
}

const styles = createStyles({
  tableRow: {
    cursor: "pointer"
  },
  textRight: {
    textAlign: "right"
  },
  wideColumn: {
    width: "80%"
  }
});
const TranslationsEntitiesList = withStyles(styles, {
  name: "TranslationsEntitiesList"
})(
  ({
    classes,
    disabled,
    entities,
    onNextPage,
    onPreviousPage,
    onRowClick,
    pageInfo
  }: TranslationsEntitiesListProps & WithStyles<typeof styles>) => (
    <Table>
      <TableHead>
        <TableRow>
          <TableCell className={classes.wideColumn}>
            {i18n.t("Name", { context: "table header" })}
          </TableCell>
          <TableCell className={classes.textRight}>
            {i18n.t("Completed Translations", {
              context: "table header"
            })}
          </TableCell>
        </TableRow>
      </TableHead>
      <TableFooter>
        <TableRow>
          <TablePagination
            colSpan={2}
            hasNextPage={
              pageInfo && !disabled ? pageInfo.hasNextPage : undefined
            }
            onNextPage={onNextPage}
            hasPreviousPage={
              pageInfo && !disabled ? pageInfo.hasPreviousPage : undefined
            }
            onPreviousPage={onPreviousPage}
          />
        </TableRow>
      </TableFooter>
      <TableBody>
        {renderCollection(
          entities,
          entity => (
            <TableRow
              className={classNames({
                [classes.tableRow]: !!entity
              })}
              hover={!!entity}
              onClick={entity ? () => onRowClick(entity.id) : undefined}
              key={entity ? entity.id : "skeleton"}
            >
              <TableCell>
                {maybe<React.ReactNode>(() => entity.name, <Skeleton />)}
              </TableCell>
              <TableCell className={classes.textRight}>
                {maybe<React.ReactNode>(
                  () =>
                    i18n.t("{{ current }} of {{ max }}", {
                      context: "translation progress",
                      ...entity.completion
                    }),
                  <Skeleton />
                )}
              </TableCell>
            </TableRow>
          ),
          () => (
            <TableRow>
              <TableCell colSpan={2}>
                {i18n.t("No translatable entities found")}
              </TableCell>
            </TableRow>
          )
        )}
      </TableBody>
    </Table>
  )
);
TranslationsEntitiesList.displayName = "TranslationsEntitiesList";
export default TranslationsEntitiesList;
