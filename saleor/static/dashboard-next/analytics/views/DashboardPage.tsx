import * as moment from 'moment';
import * as React from "react";

import CardSpacer from "../../components/CardSpacer";
import Container from "../../components/Container";
import PageHeader from "../../components/PageHeader";
import i18n from "../../i18n";

import ChartCard from "../components/ChartCard";

const cardContainerStyles = {
  display: "grid",
  gridColumnGap: "24px",
  gridTemplateColumns: "1fr 1fr",
  rowGap: "24px"
}

const timeDimensions = [{
  dateRange: [
    moment().subtract(30, 'days').format("YYYY-MM-DD"),
    moment().format("YYYY-MM-DD")
  ],
  dimension: 'Orders.created',
  granularity: 'day'
}];
const queries = [
  {
    query: {
      measures: ["Orders.count"],
      timeDimensions
    },
    title: i18n.t("Total Orders"),
    visualizationType: 'line',
  },
  {
    query: {
      measures: ["Orders.totalNet"],
      timeDimensions
    },
    title: i18n.t("Total Sales"),
    visualizationType: 'line'
  },
  {
    query: {
      measures: ["Orders.averageValue"],
      timeDimensions
    },
    title: i18n.t("Average Order Value"),
    visualizationType: 'line'
  },
  {
    query: {
      dimensions: ["Orders.status"],
      measures: ["Orders.count"]
    },
    title: i18n.t("Orders by Status"),
    visualizationType: 'pie'
  }
];

const DashboardPage = () => (
  <Container>
    <PageHeader title={i18n.t("Analytics")} />
    <CardSpacer />
    <div style={cardContainerStyles}>
      {queries.map((query, index) => (
        <ChartCard key={index} {...query}  />
      ))}
    </div>
  </Container>
);

DashboardPage.displayName = "DashboardPage";
export default DashboardPage;
