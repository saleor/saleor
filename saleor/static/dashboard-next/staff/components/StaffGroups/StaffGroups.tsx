import Card from "@material-ui/core/Card";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import AddIcon from "@material-ui/icons/Add";
import CloseIcon from "@material-ui/icons/Close";
import * as React from "react";

import PageHeader from "../../../components/PageHeader";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";

interface StaffGroupsProps {
  groups?: Array<{
    id: string;
    name?: string;
  }>;
  disabled?: boolean;
  onGroupAdd?: () => void;
  onGroupDelete?: (id: string) => () => void;
  onRowClick?: (id: string) => () => void;
}

const decorate = withStyles(theme => ({
  link: {
    color: theme.palette.secondary.main,
    cursor: "pointer" as "pointer"
  }
}));
const StaffGroups = decorate<StaffGroupsProps>(
  ({ classes, disabled, groups, onGroupAdd, onGroupDelete, onRowClick }) => (
    <Card>
      <PageHeader title={i18n.t("Groups")}>
        <IconButton disabled={disabled || !onGroupAdd} onClick={onGroupAdd}>
          <AddIcon />
        </IconButton>
      </PageHeader>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell />
            <TableCell>{i18n.t("Name", { context: "object" })}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {groups === undefined || groups === null ? (
            <TableRow>
              <TableCell>
                <IconButton disabled>
                  <CloseIcon />
                </IconButton>
              </TableCell>
              <TableCell>
                <Skeleton />
              </TableCell>
            </TableRow>
          ) : groups.length > 0 ? (
            groups.map(group => (
              <TableRow key={group.id}>
                <TableCell>
                  <IconButton
                    disabled={disabled || !onGroupDelete}
                    onClick={
                      !!onGroupDelete ? onGroupDelete(group.id) : undefined
                    }
                  >
                    <CloseIcon />
                  </IconButton>
                </TableCell>
                <TableCell
                  onClick={!!onRowClick ? onRowClick(group.id) : undefined}
                  className={classes.link}
                >
                  {group.name}
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={1}>
                {i18n.t("This user is not a member of any group.")}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
StaffGroups.displayName = "StaffGroups";
export default StaffGroups;
