import Card from "@material-ui/core/Card";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import { ShopInfo_shop_languages } from "../../../components/Shop/types/ShopInfo";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";

export interface TranslationsLanguageListProps {
  languages: ShopInfo_shop_languages[];
  onRowClick: (code: string) => void;
}

const styles = createStyles({
  capitalize: {
    textTransform: "capitalize"
  },
  link: {
    cursor: "pointer"
  }
});

const TranslationsLanguageList = withStyles(styles, {
  name: "TranslationsLanguageList"
})(
  ({
    classes,
    languages,
    onRowClick
  }: TranslationsLanguageListProps & WithStyles<typeof styles>) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>
              {i18n.t("Language", { context: "table header" })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {renderCollection(
            languages,
            language => (
              <TableRow
                className={!!language ? classes.link : undefined}
                hover={!!language}
                key={language ? language.code : "skeleton"}
                onClick={() => onRowClick(language.code)}
              >
                <TableCell className={classes.capitalize}>
                  {maybe<React.ReactNode>(
                    () => language.language,
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={1}>
                  {i18n.t("No languages found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
TranslationsLanguageList.displayName = "TranslationsLanguageList";
export default TranslationsLanguageList;
