# Script for Kaggel Titanic Competitions
# Author: Manuel Spierenburg


import AutoClassifiers
import AutoLinear
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingClassifier

# config
# number of folds in cross validation
n_folds = 10

train_file = './data/train.csv'
test_file = './data/test.csv'

#####################
# prepare data
#####################
train = pd.read_csv(train_file)
test = pd.read_csv(test_file)
total = pd.concat([train, test])


#####################
# data cleansing 
#####################

# extract title from name attribute
titles = [n.split(',')[1].split('.')[0].strip() for n in total.Name]
total['Title'] = titles
total.Title.value_counts()

# convert title to numeric value
title_map =  {v: k for k,v in enumerate(np.unique(titles))}
total.Title = total.Title.map(title_map).astype(int)

# change sex to boolean 
total['Sex'] = total['Sex'] == 'male'

# create new family features
total['FamilySize'] = total.SibSp + total.Parch
total['IsAlone'] = total['FamilySize'] == 0

# fill missing Fare value with 0
total.Fare.fillna(0, inplace=True)
total.Embarked.fillna('S', inplace=True)
emb_map =  {v: k for k,v in enumerate(np.unique(total.Embarked))}
total.Embarked = total.Embarked.map(emb_map).astype(int)


# predict age for missing rows with linear regression
x_withAge = total[~total.Age.isnull()]
fts = ['Pclass','Sex','SibSp','Parch','Fare', 'Title']
# test different linear models
AutoLinear.run_simple(x_withAge[fts], x_withAge.Age)
m = LinearRegression()
m.fit(x_withAge[fts], x_withAge.Age)
x_withoutAge = total[total.Age.isnull()]
y = m.predict(x_withoutAge[fts])
total.loc[total.Age.isnull(), 'Age'] = y

# set age for missing with mean
#total.Age.fillna(total.Age.mean(), inplace=True)

# select features
fts = ['Pclass','Sex','Age','SibSp','Parch','Fare', 'Title', 'FamilySize', 
       'IsAlone', 'Embarked']
X_total = total[fts]

# split in train and test
X_train = X_total[:len(train)]
X_test = X_total[len(train):]


#####################
# visualiziation 
#####################


survived = train.Survived

# plot relationships
plt.figure()
sns.countplot(x="Sex", hue="Survived",  data=train)
# female are more likely to survive

plt.figure()
plt.hist([X_train[train.Survived == 1].Age, X_train[train.Survived == 0].Age], 
         stacked=True, bins=30, color=['g','r'], label=['Survived','Died'])
# children <= 10 more likely to survive

plt.figure()
plt.hist([X_train[train.Survived == 1].Fare, X_train[train.Survived == 0].Fare], 
         stacked=True, bins=30, color=['g','r'], label=['Survived','Died'])
# higher fare >~70 more likely to survive

plt.figure()
sns.boxplot(x='Survived', y='Age', data=train)
plt.figure()
sns.countplot(x="SibSp", hue="Survived",  data=train)
plt.figure()
sns.countplot(x="Parch", hue="Survived",  data=train)
plt.figure()
sns.countplot(x="Pclass", hue="Survived",  data=train)
plt.figure()
sns.countplot(x="Embarked", hue="Survived",  data=train)
plt.show()

#####################
# model selection
#####################
AutoClassifiers.run(X_train, train.Survived, n_folds)

#######################
# use classifier for submisison
#######################
m = GradientBoostingClassifier(n_estimators =20, 
                               max_depth=5)
m.fit(X_train, train.Survived)
s = m.score(X_train, train.Survived)
print("score: ", s)
y_test = m.predict(X_test)

sub = pd.DataFrame({"PassengerId": test.PassengerId, "Survived": y_test})
sub.to_csv("submission_gradient_boost.csv", index=False)
