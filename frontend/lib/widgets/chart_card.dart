import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

enum ChartType { pie, bar, line }

class ChartCard extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget chart;
  final ChartType chartType;
  final List<ChartLegendItem>? legendItems;
  final VoidCallback? onTap;

  const ChartCard({
    Key? key,
    required this.title,
    this.subtitle,
    required this.chart,
    required this.chartType,
    this.legendItems,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Chart title and subtitle
              Text(
                title,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (subtitle != null) ...[
                SizedBox(height: 4),
                Text(
                  subtitle!,
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey[600],
                  ),
                ),
              ],
              SizedBox(height: 16),
              
              // Chart widget
              SizedBox(
                height: 200,
                width: double.infinity,
                child: chart,
              ),
              
              // Legend (if provided)
              if (legendItems != null && legendItems!.isNotEmpty) ...[
                SizedBox(height: 16),
                ChartLegend(items: legendItems!),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class ChartLegendItem {
  final String label;
  final Color color;

  ChartLegendItem({required this.label, required this.color});
}

class ChartLegend extends StatelessWidget {
  final List<ChartLegendItem> items;

  const ChartLegend({
    Key? key,
    required this.items,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 16,
      runSpacing: 8,
      children: items.map((item) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: item.color,
                shape: BoxShape.circle,
              ),
            ),
            SizedBox(width: 6),
            Text(
              item.label,
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[700],
              ),
            ),
          ],
        );
      }).toList(),
    );
  }
}

class PieChartSample extends StatelessWidget {
  final List<PieChartSectionData> sections;

  const PieChartSample({
    Key? key,
    required this.sections,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return PieChart(
      PieChartData(
        sectionsSpace: 0,
        centerSpaceRadius: 40,
        sections: sections,
        borderData: FlBorderData(show: false),
      ),
    );
  }
}

class BarChartSample extends StatelessWidget {
  final List<BarChartGroupData> barGroups;
  final List<String> titles;
  final double? maxY;

  const BarChartSample({
    Key? key,
    required this.barGroups,
    required this.titles,
    this.maxY,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return BarChart(
      BarChartData(
        alignment: BarChartAlignment.spaceAround,
        maxY: maxY,
        barTouchData: BarTouchData(enabled: false),
        titlesData: FlTitlesData(
          show: true,
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                if (value < 0 || value >= titles.length) {
                  return const Text('');
                }
                return Padding(
                  padding: const EdgeInsets.only(top: 8.0),
                  child: Text(
                    titles[value.toInt()],
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 12,
                    ),
                  ),
                );
              },
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 40,
              getTitlesWidget: (value, meta) {
                if (value == 0) {
                  return const Text('');
                }
                return Padding(
                  padding: const EdgeInsets.only(right: 8.0),
                  child: Text(
                    value.toInt().toString(),
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 12,
                    ),
                  ),
                );
              },
            ),
          ),
          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          horizontalInterval: maxY != null ? maxY! / 5 : null,
        ),
        borderData: FlBorderData(show: false),
        barGroups: barGroups,
      ),
    );
  }
}

class LineChartSample extends StatelessWidget {
  final List<LineChartBarData> lines;
  final List<String>? xLabels;
  final double? maxY;
  final String? leftTitle;
  final String? bottomTitle;
  final bool showDots;

  const LineChartSample({
    Key? key,
    required this.lines,
    this.xLabels,
    this.maxY,
    this.leftTitle,
    this.bottomTitle,
    this.showDots = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return LineChart(
      LineChartData(
        lineTouchData: LineTouchData(enabled: true),
        gridData: FlGridData(
          show: true,
          drawVerticalLine: true,
          horizontalInterval: maxY != null ? maxY! / 5 : null,
          verticalInterval: 1,
        ),
        titlesData: FlTitlesData(
          show: true,
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                if (xLabels == null || value < 0 || value >= xLabels!.length) {
                  return const Text('');
                }
                return Padding(
                  padding: const EdgeInsets.only(top: 8.0),
                  child: Text(
                    xLabels![value.toInt()],
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 10,
                    ),
                  ),
                );
              },
            ),
            axisNameWidget: bottomTitle != null
                ? Padding(
                    padding: const EdgeInsets.only(top: 16.0),
                    child: Text(
                      bottomTitle!,
                      style: TextStyle(
                        color: Colors.grey[800],
                        fontSize: 12,
                      ),
                    ),
                  )
                : null,
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 40,
              getTitlesWidget: (value, meta) {
                if (value == 0) {
                  return const Text('');
                }
                return Padding(
                  padding: const EdgeInsets.only(right: 8.0),
                  child: Text(
                    value.toInt().toString(),
                    style: TextStyle(
                      color: Colors.grey[600],
                      fontSize: 10,
                    ),
                  ),
                );
              },
            ),
            axisNameWidget: leftTitle != null
                ? Padding(
                    padding: const EdgeInsets.only(bottom: 16.0),
                    child: Text(
                      leftTitle!,
                      style: TextStyle(
                        color: Colors.grey[800],
                        fontSize: 12,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  )
                : null,
          ),
          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        borderData: FlBorderData(
          show: true,
          border: Border(
            bottom: BorderSide(color: Colors.grey.shade300),
            left: BorderSide(color: Colors.grey.shade300),
          ),
        ),
        maxY: maxY,
        lineBarsData: lines,
      ),
    );
  }
}