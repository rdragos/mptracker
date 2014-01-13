from pyquery import PyQuery as pq

class Infoarena(object):
    index_url1 = "http://www.infoarena.ro/runda/teme_acmunibuc_2013/clasament?rankings_display_entries=50&rankings_first_entry=0"
    index_url2 = "http://www.infoarena.ro/runda/teme_acmunibuc_2013/clasament?rankings_display_entries=50&rankings_first_entry=50"
    #30 - 59 5
    #>60 10p
    
    #pe fiecare grupa de problema 2/3 din probleme
    #media tutoror mai putin cel mai putin scor

    problems = [ 
            ('par', 'secv6', 'trompeta', 'cerere'),
            ('tsunami', 'alee', 'amici2'),
            ('struti'),
            ('adapost2', 'matrice2'),
            ('radio2', 'patrate3', 'map', 'substr'),
            ('berarii2', 'markon', 'reinvent'),
            ('sate', 'cezar', 'apdm'),
            ('cristale', 'int', 'elimin', 'elmaj', 'aprindere', 'farfurii'),
            ('permut', 'magicmatrix', 'kami', 'mission', '3color')
        ]

    score_set = []
    user_set = []

    def fetch_users(self, index_url):
        #url_set = self.fetch_urls(self.index_url)
        page = pq(index_url)
        users = page('table.sortable .normal-user .username a') 
        scores = page('table.sortable').find('.number.score')
        
        for i in range(len(users)):
            self.user_set.append(users.eq(i).text())
        for i in range(len(scores)):
            if i == 0:
                continue
            self.score_set.append(scores.eq(i).text())
            
        #from pdb import set_trace; set_trace()
        
    def getscore(self, problem, user): 
        user_page = pq('http://www.infoarena.ro/runda/teme_acmunibuc_2013?user='+user) 
        
        v = user_page('table.sortable .task a')
        import pdb;
        pdb.set_trace();
        v = list(filter(lambda element : pq(element).attr('href').split('/')[-1] == problem, v))
        pdb.set_trace()
        v[0] = pq(v[0]).parent().parent().parent().find('.score').text()
        
        pdb.set_trace()

        
    def go_scrape(self):
        """
        self.fetch_users(self.index_url1)
        self.fetch_users(self.index_url2)
        self.getscore('secv6', 'freak93')
        """

        
        D = dict()
        total_problems = self.problems
        
        for user in user_set:
            v = []
            for problem_group in total_problems:
                points = 0           
                for problem in problem_group:
                    temp_score = getscore(problem, user)
                    if temp_score >= 30 and temp_score < 60:
                        points += 5
                    if temp_score > 60:
                        points += 10
                v.append(points * 2 / 3)
            v.sort()

            for i in range(1, len(v)):
                total_score += v[i]
            total_score /= (len(v) - 1)
            D.update({user: total_score})
        """
        import pdb; pdb.set_trace()
        import json
        f = open("dump-result.json", "w")
        json.dump( D, f)

