from flask import Blueprint
from flask import Flask, render_template, request
import json
from collections import defaultdict
from datetime import datetime


class Hotkeys:

    def __init__(self, database, cache):
        self.db = database
        self.cache = cache
        self.bp = Blueprint('hotkeys', __name__, static_folder='static', static_url_path='/hotkeys/static',
                            template_folder='templates')

        # Routes should be set explicity, because Flask process self parameter in function wrong.
        self.bp.add_url_rule("/", view_func=self.index)
        self.bp.add_url_rule("/profiles_tws", view_func=self.set_profile_tws)
        self.bp.add_url_rule("/info/<ip>", view_func=self.set_ip_info)
        self.bp.add_url_rule("/outtuples/<profile>/<timewindow>", view_func=self.set_outtuples)
        self.bp.add_url_rule("/intuples/<profile>/<timewindow>", view_func=self.set_intuples)
        # TODO: decide and fix the graph
        # self.bp.add_url_rule("/dstIP/<profile>/<timewindow>", view_func=self.set_DstIPflow)
        # self.bp.add_url_rule("/DstPortsClientUDPNotEstablished", view_func=self.set_dstPortsClientUDPNotEstablished)
        self.bp.add_url_rule("/timeline_flows/<profile>/<timewindow>", view_func=self.set_timeline_flows)
        self.bp.add_url_rule("/timeline/<profile>/<timewindow>", view_func=self.set_timeline)
        self.bp.add_url_rule("/timeline/<profile>/<timewindow>/<search_filter>", view_func=self.set_timeline)
        self.bp.add_url_rule("/alerts/<profile>/<timewindow>", view_func=self.set_alerts)
        self.bp.add_url_rule("/evidence/<profile>/<timewindow>/<alert_id>", view_func=self.set_evidence)

    def ts_to_date(self, ts, seconds=False):
        if seconds:
            return datetime.fromtimestamp(ts).strftime('%Y/%m/%d %H:%M:%S.%f')
        return datetime.fromtimestamp(ts).strftime('%Y/%m/%d %H:%M:%S')

    def format_tw(self, profile, tw, seconds=False):
        tw_tuple = self.db.zrange("tws" + profile, 0, -1, withscores=True)
        tw_n = tw_tuple[0]
        tw_ts = tw_tuple[1]
        tw_date = self.ts_to_date(tw_ts)
        return "TW" + " " + tw_n.split("timewindow")[1] + ":" + tw_date

    def get_all_tw_with_ts(self, profileid):
        tws = self.db.zrange("tws" + profileid, 0, -1, withscores=True)
        dict_tws = defaultdict(dict)

        for tw_tuple in tws:
            tw_n = tw_tuple[0]
            tw_ts = tw_tuple[1]
            tw_date = self.ts_to_date(tw_ts)
            dict_tws[tw_n]["name"] = "TW" + " " + tw_n.split("timewindow")[1] + ":" + tw_date
            dict_tws[tw_n]["blocked"] = False  # needed to color profiles
        return dict_tws

    def index(self):
        return render_template('hotkeys.html', title='Slips')

    def get_ip_info(self, ip):
        """
        Retrieve IP information from database
        :param ip: active IP
        :return: all data about the IP in database
        """
        data = {'geocountry': "-", 'asnorg': "-", 'reverse_dns': "-", "threat_intel":"-", "url": "-", "down_file": "-", "ref_file": "-",
                "com_file": "-"}
        ip_info = self.cache.hget('IPsInfo', ip)
        if ip_info:
            ip_info = json.loads(ip_info)
            # Hardcoded decapsulation due to the complexity of data in side. Ex: {"asn":{"asnorg": "CESNET", "timestamp": 0.001}}
            geocountry = ip_info.get('geocountry', '-')
            asn = ip_info.get('asn', False)
            asnorg = [asn.get('asnorg', '-') if asn else '-']
            reverse_dns = ip_info.get('reverse_dns', '-')

            threatintel = ip_info.get('threatintelligence', False)
            threatintel_info = [threatintel.get('description', '-') + "," + threatintel.get('threat_level', '-') + " threat level" if threatintel else '-']

            vt_scores = ip_info.get("VirusTotal", False)
            url, down_file, ref_file, com_file = '-', '-', '-', '-'
            if vt_scores:
                url = vt_scores.get("URL", "-")
                down_file = vt_scores.get("down_file", "-")
                ref_file = vt_scores.get("ref_file", "-")
                com_file = vt_scores.get("com_file", "-")

            data = {'geocountry': geocountry, 'asnorg': asnorg,
                    'reverse_dns': reverse_dns,
                    'threat_intel': threatintel_info, "url": url,
                    "down_file": down_file, "ref_file": ref_file,
                    "com_file": com_file}
        return data

    def set_ip_info(self, ip):
        '''
        Set info about the ip in route /info/<ip> (geocountry, asn, TI)
        :param ip: active IP
        :return: information about IP in database
        '''
        ip_info = self.get_ip_info(ip)
        ip_info["ip"] = ip
        data = [ip_info]

        return {
            'data': data
        }

    def set_profile_tws(self):
        '''
        Set profiles and their timewindows into the tree. Blocked are highligted in red.
        :return: (profile, [tw, blocked], blocked)
        '''

        # Fetch blocked
        dict_blockedProfileTWs = defaultdict(list)
        blockedProfileTWs = self.db.hgetall('BlockedProfTW')

        if blockedProfileTWs:
            for profile, tws in blockedProfileTWs.items():
                profile_word, blocked_ip = profile.split("_")
                dict_blockedProfileTWs[blocked_ip] = json.loads(tws)

        # Fetch profiles
        profiles = self.db.smembers('profiles')
        data = []
        for profileid in profiles:
            profile_word, profile_ip = profileid.split("_")
            dict_tws = self.get_all_tw_with_ts(profileid)
            blocked_profile = False

            if profile_ip in dict_blockedProfileTWs.keys():
                for blocked_tw in dict_blockedProfileTWs[profile_ip]:
                    dict_tws[blocked_tw]["blocked"] = True
                blocked_profile = True

            data.append({"id": str(id), "profile": profile_ip, "tws": dict_tws, "blocked": blocked_profile})

        return {
            'data': data
        }

    # TODO: decide and fix the graph
    # def set_DstIPflow(self, profile, timewindow):
    #     """
    #     Set flows per each destination IP
    #     :param profile: active profile
    #     :param timewindow: active timewindow
    #     :return: data with flows per ip
    #     """
    #     dst_ips = json.loads(self.db.hget(profile + '_' + timewindow, 'DstIPs'))
    #     data = []
    #     id = 0
    #     for ip, port in dst_ips.items():
    #         data.append({"ip": ip, "flow": port})
    #         id = id + 1
    #
    #     return {
    #         'data': data
    #     }

    # TODO: decide and fix the graph
    # def set_dstPortsClientUDPNotEstablished(self):
    #
    #     dst_ips = json.loads(self.db.hget('profile_192.168.2.16_timewindow1', 'DstPortsClientUDPNotEstablished'))
    #     data = []
    #     id = 0
    #     for port, info in dst_ips.items():
    #         data.append({"port": port, "info": info})
    #         id = id + 1
    #
    #     return {
    #         'data': data
    #     }

    def set_outtuples(self, profile, timewindow):
        """
        Set outtuples of a chosen profile and timewindow.
        :param profile: active profile
        :param timewindow: active timewindow
        :return: (tuple, key, ip_info)
        """

        data = []
        outtuples = self.db.hget(profile + '_' + timewindow, 'OutTuples')
        if outtuples:
            outtuples = json.loads(outtuples)

            for key, value in outtuples.items():
                ip, port, protocol = key.split("-")
                ip_info = self.get_ip_info(ip)
                outtuple_dict = dict()
                outtuple_dict.update({'tuple': key, 'string': value[0]})
                outtuple_dict.update(ip_info)
                data.append(outtuple_dict)

        return {
            'data': data
        }

    def set_intuples(self, profile, timewindow):
        """
        Set intuples of a chosen profile and timewindow.
        :param profile: active profile
        :param timewindow: active timewindow
        :return: (tuple, string, ip_info)
        """
        data = []
        intuples = self.db.hget(profile + '_' + timewindow, 'InTuples')
        if intuples:
            intuples = json.loads(intuples)
            for key, value in intuples.items():
                ip, port, protocol = key.split("-")
                ip_info = self.get_ip_info(ip)

                outtuple_dict = dict()
                outtuple_dict.update({'tuple': key, 'string': value[0]})
                outtuple_dict.update(ip_info)
                data.append(outtuple_dict)

        return {
            'data': data
        }

    def set_timeline_flows(self, profile, timewindow):
        """
        Set timeline flows of a chosen profile and timewindow.
        :return: list of timeline flows as set initially in database
        """
        data = []
        timeline_flows = self.db.hgetall(profile + "_" + timewindow + "_flows")
        if timeline_flows:
            for key, value in timeline_flows.items():
                value = json.loads(value)

                # convert timestamp to date
                timestamp = value["ts"]
                dt_obj = self.ts_to_date(timestamp, seconds=True)
                value["ts"] = dt_obj

                # limit duration decimals
                duration = float(value["dur"])
                value["dur"] = "{:.5f}".format(duration)

                data.append(value)

        return {
            'data': data
        }

    def set_timeline(self, profile, timewindow, search_filter=""):
        """
        Set timeline data of a chosen profile and timewindow
        :return: list of timeline as set initially in database
        """
        data = []

        timeline = self.db.zrange(profile + "_" + timewindow + "_timeline", 0, -1)
        if timeline:

            search_filter = search_filter.strip()
            search = True if search_filter else False
            reverse = False
            if search and "!" in search_filter:
                search_filter = search_filter.replace("!", "")
                reverse = True

            for flow in timeline:
                flow = json.loads(flow)

                # TODO: check this logic
                if flow["preposition"] == "from":
                    temp = flow["saddr"]
                    flow["daddr"] = temp

                # fix State string TODO: fix in slips code
                if flow["state"] == "notestablished":
                    flow["state"] = "not established"

                # search
                if not search:
                    data.append(flow)
                else:
                    value_is_present = False

                    # partial search in each flow key
                    for v in flow.values():
                        if search_filter.lower() in str(v).lower():
                            value_is_present = True
                            break

                    if (not reverse and value_is_present) or (reverse and not value_is_present):
                        data.append(flow)

        return {
            'data': data
        }

    def set_alerts(self, profile, timewindow):
        """
        Set alerts for chosen profile and timewindow
        """
        data = []
        alerts = self.db.hget("alerts", profile)

        if alerts:
            alerts = json.loads(alerts)
            alerts_tw = alerts[timewindow]
            tws = self.get_all_tw_with_ts(profile)
            evidences = self.db.hget("evidence" + profile, timewindow)
            evidences = json.loads(evidences)

            for alert_ID, evidence_ID_list in alerts_tw.items():
                evidence_count = len(evidence_ID_list)
                alert_description = json.loads(evidences[alert_ID])
                alert_timestamp = alert_description["stime"]
                if not isinstance(alert_timestamp, str): # add check if the timestamp is a string
                    alert_timestamp = self.ts_to_date(alert_description["stime"], seconds=True)
                profile_ip = profile.split("_")[1]
                tw_name = tws[timewindow]["name"]

                data.append(
                    {"alert": alert_timestamp, "alert_id": alert_ID, "profileid": profile_ip, "timewindow": tw_name,
                     "evidence_count": evidence_count})
        return {"data": data}

    def set_evidence(self, profile, timewindow, alert_id):
        """
        Set evidence table for the pressed alert in chosem profile and timewindow
        """

        data = []
        alerts = self.db.hget("alerts", profile)

        if alerts:
            alerts = json.loads(alerts)
            alerts_tw = alerts[timewindow]
            evidence_ID_list = alerts_tw[alert_id]
            evidences = self.db.hget("evidence" + profile, timewindow)
            evidences = json.loads(evidences)

            for evidence_ID in evidence_ID_list:
                temp_evidence = json.loads(evidences[evidence_ID])
                if "source_target_tag" not in temp_evidence:
                    temp_evidence["source_target_tag"] = "-"
                data.append(temp_evidence)
        return {"data": data}