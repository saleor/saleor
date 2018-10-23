import Card from "@material-ui/core/Card";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemText from "@material-ui/core/ListItemText";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../../components/CardTitle";
import DateFormatter from "../../../components/DateFormatter";
import Skeleton from "../../../components/Skeleton";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";

interface HomeProductListCardProps {
  activities?: Array<{
    action: string;
    admin: boolean;
    date: string;
    elementName?: string;
    id: string;
    newElement: string;
    user: string;
  }>;
  disabled: boolean;
}

const decorate = withStyles({
  loadingProducts: {
    paddingBottom: "8px",
    paddingTop: "7px"
  },
  noProducts: {
    paddingBottom: "14px",
    paddingTop: "14px"
  }
});

const HomeProductListCard = decorate<HomeProductListCardProps>(
  ({ classes, activities }) => {
    return (
      <Card>
        <CardTitle title={i18n.t("Activity")} />
        <List dense={true}>
          {renderCollection(
            activities,
            activity => (
              <ListItem key={activity ? activity.id : "skeleton"}>
                {activity ? (
                  <ListItemText
                    primary={
                      <Typography
                        dangerouslySetInnerHTML={{
                          __html: activity.admin
                            ? i18n.t(`Saleor shop admin 
                        ${activity.action} ${activity.newElement}: 
                        ${activity.user}`)
                            : i18n.t(`
                        ${activity.user} ${activity.action} a 
                        ${activity.newElement}: ${activity.elementName}
                        `)
                        }}
                      />
                    }
                    secondary={<DateFormatter date={activity.date} />}
                  />
                ) : (
                  <ListItemText className={classes.loadingProducts}>
                    <Typography>
                      <Skeleton />
                    </Typography>
                  </ListItemText>
                )}
              </ListItem>
            ),
            () => (
              <ListItem dense={false} className={classes.noProducts}>
                <ListItemText
                  primary={
                    <Typography>{i18n.t("No products found")}</Typography>
                  }
                />
              </ListItem>
            )
          )}
        </List>
      </Card>
    );
  }
);
export default HomeProductListCard;
